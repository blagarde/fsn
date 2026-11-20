"""Spectrum-averaged cross sections from ENDF/B-VIII.0.

Pipeline per nuclide:
  1. Read the single ENDF file out of NNDC's library zip with HTTP range requests (cached, hashed).
  2. Reconstruct resonances and Doppler-broaden with NJOY2016 (via openmc.data.IncidentNeutron.from_njoy).
  3. Integrate each reaction against the weighting functions defined in WEIGHTINGS.

Requires the `nuc` conda environment (NJOY2016 + OpenMC); see setup/install_env.sh.
"""
from __future__ import annotations

import re
import sqlite3
import tempfile
from pathlib import Path

import numpy as np

from ..chem import Z_OF
from ..db import ingest_run
from ..fetch import RemoteZip, fetch_member

SOURCE_ID = "endfb80"
ARCHIVE = "https://www.nndc.bnl.gov/endf-b8.0/zips/ENDF-B-VIII.0_neutrons.zip"
_MEMBER = re.compile(r"n-(\d{3})_([A-Za-z]+)_(\d{3})(m\d)?\.endf$")

K_B = 8.617333262e-5  # eV/K (CODATA 2018)
WATT_A, WATT_B = 0.988e6, 2.249e-6  # eV, 1/eV

WEIGHTINGS = {
    "thermal_2200": (
        "Value at 0.0253 eV (2200 m/s)",
        "sigma(E = 0.0253 eV), linear interpolation on the broadened pointwise grid",
        "Standard thermal reference point",
    ),
    "maxwell_flux": (
        "Maxwellian flux-weighted average at the broadening temperature",
        "int sigma(E) M(E) dE / int M(E) dE, M(E) = E exp(-E/kT), E in [1e-5, 10] eV",
        "Flux-weighted (not Westcott-convention) average",
    ),
    "ri_1overE": (
        "Infinite-dilution resonance integral",
        "int_{0.5 eV}^{20 MeV} sigma(E) dE/E (cadmium cut-off 0.5 eV)",
        "Conventional definition, e.g. as used in Mughabghab's Atlas",
    ),
    "watt_u235": (
        "U-235 thermal-fission spectrum average",
        "int sigma(E) chi(E) dE / int chi(E) dE, chi(E) = exp(-E/a) sinh(sqrt(b E)), a = 0.988 MeV, b = 2.249 /MeV, E in [1e-5 eV, 20 MeV]",
        "Watt parameters for thermal fission of U-235 as tabulated in the MCNP manual (verify)",
    ),
}


def archive_index(rz: RemoteZip) -> dict[tuple[int, int], str]:
    index = {}
    for name in rz.names():
        m = _MEMBER.search(name)
        if m and not m.group(4):  # ground states only
            index[(int(m.group(1)), int(m.group(3)))] = name
    return index


def _grid(x: np.ndarray, lo: float, hi: float, n_log: int = 4000) -> np.ndarray:
    g = np.union1d(x[(x >= lo) & (x <= hi)], np.geomspace(lo, hi, n_log))
    return g


def averages(xs, temperature_K: float) -> dict[str, float]:
    """xs: callable Tabulated1D-like with .x energies (eV). Returns value per weighting id."""
    x = np.asarray(xs.x)
    out = {"thermal_2200": float(xs(0.0253))}

    kT = K_B * temperature_K
    e = _grid(x, 1e-5, 10.0)
    w = e * np.exp(-e / kT)
    out["maxwell_flux"] = float(np.trapezoid(xs(e) * w, e) / np.trapezoid(w, e))

    e = _grid(x, 0.5, min(2.0e7, x.max()))
    out["ri_1overE"] = float(np.trapezoid(xs(e) / e, e))

    e = _grid(x, 1e-5, min(2.0e7, x.max()))
    w = np.exp(-e / WATT_A) * np.sinh(np.sqrt(WATT_B * e))
    out["watt_u235"] = float(np.trapezoid(xs(e) * w, e) / np.trapezoid(w, e))
    return out


def _reaction_xs(data, mt: int, tkey: str):
    try:
        rx = data[mt]
    except (KeyError, IndexError, ValueError):
        return None
    xs = rx.xs.get(tkey) if hasattr(rx, "xs") else None
    if xs is None or not hasattr(xs, "x"):
        return None  # e.g. a Sum object without a tabulated grid
    return xs


NJOY_METHOD = "NJOY2016 RECONR+BROADR via openmc.data.IncidentNeutron.from_njoy; trapezoid on union grid"
DIRECT_METHOD = ("openmc.data.IncidentNeutron.from_endf, pointwise MF3 used as evaluated (file has no resolved or "
                 "unresolved resonance parameters); unbroadened; trapezoid on union grid")


def process(endf_path: Path, temperature_K: float, workdir: Path):
    """Return (data, temperature key, method). Falls back to reading the ENDF file directly only when NJOY
    fails AND the evaluation carries no resonance parameters, so nothing needs reconstructing."""
    import subprocess

    import openmc.data  # imported lazily: only this ingester needs the conda environment

    try:
        data = openmc.data.IncidentNeutron.from_njoy(
            str(endf_path), temperatures=[temperature_K], heatr=False, gaspr=False, purr=False,
            stdout=False, output_dir=str(workdir),
        )
        return data, data.temperatures[0], NJOY_METHOD
    except subprocess.CalledProcessError:
        data = openmc.data.IncidentNeutron.from_endf(str(endf_path))
        ranges = data.resonances.ranges if data.resonances else []
        if any(type(r) is not openmc.data.ResonanceRange for r in ranges):
            raise  # resonance parameters present: a direct read would be wrong
        return data, data.temperatures[0], DIRECT_METHOD


def ingest(con: sqlite3.Connection, targets: dict, reactions: dict[int, str], temperature_K: float,
           only: list[str] | None = None, refresh: bool = False, log=print,
           all_in_library: bool = False, skip_existing: bool = False) -> int:
    """Process the configured targets, or with all_in_library every ground-state evaluation in the archive.
    skip_existing leaves out nuclides that already have every configured reaction-independent marker (MT 101)."""
    for wid, (desc, definition, ref) in WEIGHTINGS.items():
        con.execute("INSERT OR REPLACE INTO weighting VALUES (?,?,?,?)", (wid, desc, definition, ref))
    con.commit()

    with ingest_run(con, "endf_xs_all" if all_in_library else "endf_xs") as info:
        rz = RemoteZip(ARCHIVE)
        index = archive_index(rz)
        if all_in_library:
            symbol = {z: s for s, z in Z_OF.items()}
            wanted = [(z, a, f"{symbol[z]}-{a}") for z, a in sorted(index) if z in symbol]
        else:
            wanted = [(Z_OF[el], a, f"{el}-{a}") for group in targets.values() for el, masses in group.items() for a in masses]
        if only:
            keep = {s.lower() for s in only}
            wanted = [w for w in wanted if w[2].lower() in keep or w[2].split("-")[0].lower() in keep]
        if skip_existing:
            done = {(r[0], r[1]) for r in con.execute("SELECT DISTINCT z, a FROM xs_avg WHERE mt=101 AND library=?", (SOURCE_ID,))}
            wanted = [w for w in wanted if (w[0], w[1]) not in done]
        log(f"  {len(wanted)} evaluations to process")
        missing, failed, n = [], [], 0
        for z, a, label in wanted:
            member = index.get((z, a))
            if member is None:
                missing.append(label)
                continue
            try:
                artifact_id, path = fetch_member(con, SOURCE_ID, rz, member, refresh=refresh)
                with tempfile.TemporaryDirectory() as tmp:
                    data, tkey, method = process(path, temperature_K, Path(tmp))
                rows = []
                for mt, name in reactions.items():
                    xs = _reaction_xs(data, mt, tkey)
                    if xs is None:
                        continue
                    for wid, value in averages(xs, temperature_K).items():
                        rows.append((z, a, SOURCE_ID, mt, name, wid, temperature_K, value, method, artifact_id))
                con.executemany("INSERT OR REPLACE INTO xs_avg VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
                con.commit()
                n += len(rows)
                log(f"  {label}: {len(rows)} values" + ("" if method == NJOY_METHOD else " (direct read, no NJOY)"))
            except Exception as exc:  # keep going; record the failure
                failed.append(f"{label} ({type(exc).__name__}: {exc})")
                log(f"  {label}: FAILED {exc}")
        info["rows"] = n
        info["message"] = "; ".join(
            x for x in (f"not in library: {', '.join(missing)}" if missing else "",
                        f"failed: {', '.join(failed)}" if failed else "") if x)
    return n

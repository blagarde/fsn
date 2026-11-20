"""Build an OpenMC (HDF5) neutron cross-section library from the cached ENDF/B-VIII.0 evaluations.

Each nuclide is processed with NJOY2016 (RECONR, BROADR, PURR for unresolved-resonance
probability tables, ACER) at the temperatures in config/targets.yaml (openmc_library), in
parallel, and indexed in data/openmc/cross_sections.xml. Evaluations come from the provenance
cache (artifact table), so the library traces back to the same files as the database.

Usage: python tools/openmc_library/build.py [--jobs 4] [--only U-235 Fe-56]
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "openmc"
sys.path.insert(0, str(ROOT))
from htfbr_data.chem import Z_OF  # noqa: E402


def wanted(cfg):
    for group in cfg["openmc_library"]["nuclides"].values():
        for el, masses in group.items():
            for a in masses:
                yield el, a


def endf_path(con, el, a):
    member = f"n-{Z_OF[el]:03d}_{el}_{a:03d}.endf"
    row = con.execute("SELECT local_path FROM artifact WHERE source_id='endfb80' AND member LIKE ? ORDER BY artifact_id DESC LIMIT 1",
                      (f"%{member}",)).fetchone()
    return Path(row[0]) if row else None


def work(args):
    el, a, path, temps = args
    import openmc.data
    t0 = time.time()
    out = OUT / f"{el}{a}.h5"
    if out.exists():
        return el, a, "exists", 0.0
    try:
        with tempfile.TemporaryDirectory() as tmp:
            data = openmc.data.IncidentNeutron.from_njoy(
                str(path), temperatures=temps, purr=(a >= 220), heatr=False, gaspr=False,
                stdout=False, output_dir=tmp)
        data.export_to_hdf5(str(out), "w")
        return el, a, "ok", time.time() - t0
    except Exception as exc:
        # Fallback for evaluations NJOY rejects but which carry no resonance parameters (e.g. B-10)
        try:
            data = openmc.data.IncidentNeutron.from_endf(str(path))
            ranges = data.resonances.ranges if data.resonances else []
            if any(type(r) is not openmc.data.ResonanceRange for r in ranges):
                raise exc
            data.export_to_hdf5(str(out), "w")
            return el, a, "ok (direct read, 0 K)", time.time() - t0
        except Exception as exc2:
            return el, a, f"FAILED {type(exc2).__name__}: {str(exc2)[:120]}", time.time() - t0


def index():
    import openmc.data
    lib = openmc.data.DataLibrary()
    for h5 in sorted(OUT.glob("*.h5")):
        lib.register_file(str(h5))
    lib.export_to_xml(str(OUT / "cross_sections.xml"))
    return len(lib.libraries)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    cfg = yaml.safe_load((ROOT / "config" / "targets.yaml").read_text())
    temps = cfg["openmc_library"]["temperatures_K"]
    OUT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ROOT / "data" / "htfbr.sqlite")
    tasks, missing = [], []
    for el, mass in wanted(cfg):
        if a.only and f"{el}-{mass}" not in a.only and el not in a.only:
            continue
        p = endf_path(con, el, mass)
        (tasks.append((el, mass, p, temps)) if p else missing.append(f"{el}-{mass}"))
    print(f"{len(tasks)} nuclides at {temps} K; not in cache: {missing or 'none'}", flush=True)
    with mp.Pool(a.jobs) as pool:
        for el, mass, status, dt in pool.imap_unordered(work, tasks):
            print(f"  {el}-{mass}: {status} ({dt:.0f} s)", flush=True)
    print(f"indexed {index()} nuclides in {OUT / 'cross_sections.xml'}", flush=True)


if __name__ == "__main__":
    main()

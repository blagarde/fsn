"""Thin extension of analysis/common/infinite.screen that also returns the flux spectrum and total
production/absorption tallies, plus a first-order B-10 correction.

Why: B-10 is missing from the project OpenMC library (NJOY 2016 ACER stops on the ENDF/B-VIII.0 B-10
evaluation: "Undefined law for dlwh block", see reports/openmc_library.log). ZrB2 cases are therefore
transported with all boron as B-11, and the B-10 absorption is added afterwards by first-order
perturbation: Delta A = N_B10 * sum_g sigma_abs,g(B-10) * phi_g, and k' = P / (A + Delta A), i.e.
Delta rho = -Delta A / P. sigma_abs(B-10) is read pointwise from the ENDF/B-VIII.0 file (0 K; B-10 has no
resonance parameters, so Doppler is irrelevant) and averaged over each of the 300 tally groups with a
1/E weight. The spectrum is held fixed, so for large B-10 loadings (natural boron) the magnitude is an
overestimate (no self-shielding or spectral hardening).

The model (homogeneous mix, reflective 2 cm box, settings, tallies) is identical to infinite.screen.
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np
import openmc

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "analysis" / "common"))
import infinite as INF  # noqa: E402

EDGES = np.logspace(-5, np.log10(2e7), 301)


def screen_spec(components, T, particles=20000, batches=60, inactive=20, threads=1, label="case"):
    mats = [m for m, _ in components]
    fr = np.array([f for _, f in components], dtype=float)
    mix = openmc.Material.mix_materials(mats, list(fr / fr.sum()), "vo")
    mix.temperature = T
    mix.name = label
    dens = mix.get_nuclide_atom_densities()
    nuclides = sorted(dens)
    box = openmc.model.RectangularParallelepiped(-1, 1, -1, 1, -1, 1, boundary_type="reflective")
    cell = openmc.Cell(fill=mix, region=-box)
    cell.temperature = T
    t_rates = openmc.Tally(name="rates")
    t_rates.nuclides = nuclides
    t_rates.scores = ["absorption", "fission", "(n,gamma)", "nu-fission"]
    t_flux = openmc.Tally(name="spectrum")
    t_flux.filters = [openmc.EnergyFilter(EDGES)]
    t_flux.scores = ["flux"]
    model = openmc.Model(openmc.Geometry([cell]), openmc.Materials([mix]),
                         INF._settings(T, particles, batches, inactive),
                         tallies=openmc.Tallies([t_rates, t_flux]))
    model.materials.cross_sections = str(INF.XS)
    with tempfile.TemporaryDirectory() as tmp:
        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            sp_path = model.run(threads=threads, output=False)
            with openmc.StatePoint(sp_path) as sp:
                keff = sp.keff
                rates = sp.get_tally(name="rates")
                flux = sp.get_tally(name="spectrum").mean.ravel()
                per = {n: {s: float(rates.get_values(nuclides=[n], scores=[s]).ravel()[0])
                           for s in ("absorption", "fission", "(n,gamma)", "nu-fission")} for n in nuclides}
        finally:
            os.chdir(cwd)
    fissile_abs = sum(per[n]["absorption"] for n in INF.FISSILE if n in per)
    fertile_cap = sum(per[n]["absorption"] - per[n]["fission"] for n in INF.FERTILE if n in per)
    total_abs = sum(v["absorption"] for v in per.values()) or 1.0
    parasitic = {n: v["absorption"] / total_abs for n, v in per.items() if n not in INF.FISSILE + INF.FERTILE}
    cdf = np.cumsum(flux) / flux.sum()
    return {
        "label": label, "T_K": T, "k_inf": float(keff.nominal_value), "k_inf_sd": float(keff.std_dev),
        "conversion_ratio": fertile_cap / fissile_abs if fissile_abs else float("nan"),
        "median_energy_eV": float(EDGES[1:][np.searchsorted(cdf, 0.5)]),
        "parasitic_absorption_share": dict(sorted(parasitic.items(), key=lambda kv: -kv[1])[:8]),
        "temperature_note": "" if INF.LIB_T[0] <= T <= INF.LIB_T[1] else "T outside library; nearest used",
        "nuclides": len(nuclides),
        "total_absorption": total_abs,
        "total_nu_fission": sum(v["nu-fission"] for v in per.values()),
        "flux": flux.tolist(),
        "B11_atom_density": float(dens.get("B11", 0.0)),
    }


@lru_cache(maxsize=1)
def b10_group_xs() -> np.ndarray:
    """300-group B-10 absorption (all neutron-disappearance MTs 102-117), 1/E weighted, barns."""
    import openmc.data
    con = sqlite3.connect(ROOT / "data" / "htfbr.sqlite")
    path = con.execute("SELECT local_path FROM artifact WHERE member LIKE '%n-005_B_010.endf'").fetchone()[0]
    d = openmc.data.IncidentNeutron.from_endf(path)
    E = np.logspace(-5, np.log10(2e7), 200001)
    sig = np.zeros_like(E)
    for mt in range(102, 118):
        if mt in d.reactions:
            xs = d.reactions[mt].xs["0K"]
            sig += np.where((E >= xs.x[0]) & (E <= xs.x[-1]), xs(E), 0.0)
    g = np.zeros(300)
    w = 1 / E
    for i in range(300):
        m = (E >= EDGES[i]) & (E < EDGES[i + 1])
        g[i] = np.trapezoid(sig[m] * w[m], E[m]) / np.trapezoid(w[m], E[m])
    return g


def b10_correction(res: dict, b10_fraction: float) -> dict:
    """Add B-10 at atom fraction b10_fraction of all boron (transport run had all boron as B-11)."""
    n_b = res["B11_atom_density"]
    if n_b <= 0 or b10_fraction <= 0:
        return {"b10_fraction": b10_fraction, "dA": 0.0, "drho_pcm": 0.0, "k_corrected": res["k_inf"]}
    n10 = n_b * b10_fraction
    dA = n10 * float(np.dot(b10_group_xs(), np.array(res["flux"])))
    P, A = res["total_nu_fission"], res["total_absorption"]
    k_c = res["k_inf"] * A / (A + dA)
    phi = np.array(res["flux"])
    sig_avg = float(np.dot(b10_group_xs(), phi) / phi.sum())
    return {"b10_fraction": b10_fraction, "sigma_abs_B10_spectrum_avg_b": sig_avg, "dA_over_A": dA / A, "drho_pcm": -1e5 * dA / P,
            "k_corrected": k_c, "B10_share_of_absorption": dA / (A + dA)}

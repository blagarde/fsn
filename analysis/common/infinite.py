"""Phase-1 neutronics screen: infinite homogenised medium in OpenMC.

screen(components, T) mixes the given materials by volume fraction into one homogeneous
material at temperature T, runs an eigenvalue calculation in an infinite (reflective) box, and
returns k-infinity, a conversion-ratio proxy for breeding, the flux median energy and
per-nuclide reaction rates.

This is a screening model. It ignores leakage (so k_inf overstates k_eff of a finite core by
roughly 0.1-0.3 for a large fast core), spatial self-shielding between fuel and coolant regions,
and blankets (a blanket raises the whole-core breeding ratio above the core-only value).
Use it to rank options and find feasible windows, not to size a core.

Requires data/openmc/cross_sections.xml (tools/openmc_library/build.py).
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np
import openmc

ROOT = Path(__file__).resolve().parents[2]
XS = ROOT / "data" / "openmc" / "cross_sections.xml"
LIB_T = (1200.0, 2100.0)
FISSILE = ("U233", "U235", "Pu239", "Pu241")
FERTILE = ("Th232", "U234", "U238", "Pu238", "Pu240")


def _settings(T: float, particles: int, batches: int, inactive: int) -> openmc.Settings:
    s = openmc.Settings()
    s.run_mode = "eigenvalue"
    s.particles, s.batches, s.inactive = particles, batches, inactive
    s.source = openmc.IndependentSource(space=openmc.stats.Box((-1, -1, -1), (1, 1, 1)))
    if LIB_T[0] <= T <= LIB_T[1]:
        s.temperature = {"method": "interpolation", "default": T}
    else:  # outside the library range: nearest temperature, flagged in the result
        s.temperature = {"method": "nearest", "tolerance": 1000.0, "default": T}
    s.output = {"tallies": False, "summary": False}
    return s


def screen(components: list[tuple[openmc.Material, float]], T: float, particles: int = 20000,
           batches: int = 60, inactive: int = 20, threads: int = 1, label: str = "case") -> dict:
    """components: [(material, volume fraction), ...] (fractions are renormalised). T in kelvin."""
    if not XS.exists():
        raise FileNotFoundError(f"{XS} missing: build it with tools/openmc_library/build.py")
    mats = [m for m, _ in components]
    fr = np.array([f for _, f in components], dtype=float)
    mix = openmc.Material.mix_materials(mats, list(fr / fr.sum()), "vo")
    mix.temperature = T
    mix.name = label
    nuclides = [n for n, _ in sorted(mix.get_nuclide_atom_densities().items())]

    box = openmc.model.RectangularParallelepiped(-1, 1, -1, 1, -1, 1, boundary_type="reflective")
    cell = openmc.Cell(fill=mix, region=-box)
    cell.temperature = T
    geom = openmc.Geometry([cell])

    t_rates = openmc.Tally(name="rates")
    t_rates.nuclides = nuclides
    t_rates.scores = ["absorption", "fission", "(n,gamma)", "nu-fission"]
    edges = np.logspace(-5, np.log10(2e7), 301)
    t_flux = openmc.Tally(name="spectrum")
    t_flux.filters = [openmc.EnergyFilter(edges)]
    t_flux.scores = ["flux"]

    model = openmc.Model(geom, openmc.Materials([mix]), _settings(T, particles, batches, inactive),
                         tallies=openmc.Tallies([t_rates, t_flux]))
    model.materials.cross_sections = str(XS)
    with tempfile.TemporaryDirectory() as tmp:
        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            sp_path = model.run(threads=threads, output=False)
            with openmc.StatePoint(sp_path) as sp:
                keff = sp.keff
                rates = sp.get_tally(name="rates")
                flux = sp.get_tally(name="spectrum").mean.ravel()
                def rate(nuc, score):
                    return float(rates.get_values(nuclides=[nuc], scores=[score]).ravel()[0]) if nuc in nuclides else 0.0
                per = {n: {s: rate(n, s) for s in ("absorption", "fission", "(n,gamma)", "nu-fission")} for n in nuclides}
        finally:
            os.chdir(cwd)

    fissile_abs = sum(per[n]["absorption"] for n in FISSILE if n in per)
    fertile_cap = sum(per[n]["absorption"] - per[n]["fission"] for n in FERTILE if n in per)
    total_abs = sum(v["absorption"] for v in per.values()) or 1.0
    # parasitic share: absorption in everything that is neither fissile nor fertile
    parasitic = {n: v["absorption"] / total_abs for n, v in per.items() if n not in FISSILE + FERTILE}
    cdf = np.cumsum(flux) / flux.sum()
    median_E = float(edges[1:][np.searchsorted(cdf, 0.5)])
    return {
        "label": label, "T_K": T, "k_inf": float(keff.nominal_value), "k_inf_sd": float(keff.std_dev),
        "conversion_ratio": fertile_cap / fissile_abs if fissile_abs else float("nan"),
        "median_energy_eV": median_E,
        "parasitic_absorption_share": dict(sorted(parasitic.items(), key=lambda kv: -kv[1])[:8]),
        "temperature_note": "" if LIB_T[0] <= T <= LIB_T[1] else f"T outside library {LIB_T}; nearest temperature used",
        "nuclides": len(nuclides),
    }


def void_worth(components, coolant_index: int, T: float, density_factor: float = 0.0, **kw) -> dict:
    """Reactivity change (pcm) when the coolant (components[coolant_index]) density is scaled."""
    base = screen(components, T, label="nominal", **kw)
    comps = [(m, f * (density_factor if i == coolant_index else 1.0)) for i, (m, f) in enumerate(components)]
    # keep the other volume fractions fixed: add void for the removed coolant volume
    void = openmc.Material(name="void-filler")
    void.add_nuclide("He4", 1.0)
    void.set_density("g/cm3", 1e-9)
    removed = components[coolant_index][1] * (1 - density_factor)
    comps.append((void, removed))
    pert = screen(comps, T, label=f"coolant x{density_factor}", **kw)
    rho = lambda k: (k - 1) / k
    return {"nominal": base, "perturbed": pert,
            "worth_pcm": 1e5 * (rho(pert["k_inf"]) - rho(base["k_inf"]))}

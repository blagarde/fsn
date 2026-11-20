"""Family B (seed branches B1-B6): shared material definitions and an extended infinite-medium screen.

All compositions, volume fractions and densities here are screening assumptions (approx.) and are
listed in DESIGNS so the README and the design pages can quote them. Neutronics uses
analysis/common/infinite.py conventions (same settings, same conversion-ratio proxy); screen_plus()
reproduces infinite.screen() and adds tallies (tritium, (n,p), per-nuclide capture by element).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import openmc

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "analysis" / "common"))
import infinite  # noqa: E402  (shared screening tool)

# ---- common assumptions (task brief) -------------------------------------------------------
PU_VECTOR = {"Pu238": 0.02, "Pu239": 0.60, "Pu240": 0.24, "Pu241": 0.09, "Pu242": 0.05}  # reactor-grade (approx.)
U_VECTOR = {"U235": 0.0025, "U238": 0.9975}  # depleted uranium
ENRICH = {"N15": 0.999, "Li7": 0.9999, "Cl37": 0.99}  # best achievable (P3)
NAT = {"N15": 0.003795, "Li7": 0.9515, "Cl37": 0.242}  # natural abundance (db: nuclide table, LiveChart)
# W isotopes: natural abundance (db) and an assumed 95% enrichment (approx.; no target given in the brief)
W_NAT = {"W180": 0.0012, "W182": 0.265, "W183": 0.1431, "W184": 0.3064, "W186": 0.2843}


def _heavy_metal(m: openmc.Material, pu_frac: float, per_hm: float = 1.0):
    for n, f in U_VECTOR.items():
        m.add_nuclide(n, per_hm * (1 - pu_frac) * f, "ao")
    for n, f in PU_VECTOR.items():
        m.add_nuclide(n, per_hm * pu_frac * f, "ao")


def fuel_nitride(pu_frac: float, density: float = 13.0, n15: float = ENRICH["N15"]) -> openmc.Material:
    """(U,Pu)N; 13.0 g/cm3 ~ 91% of ~14.3 g/cm3 theoretical (approx.)."""
    m = openmc.Material(name=f"(U,Pu)N x={pu_frac:.3f}")
    _heavy_metal(m, pu_frac)
    m.add_nuclide("N15", n15, "ao")
    m.add_nuclide("N14", 1 - n15, "ao")
    m.set_density("g/cm3", density)
    return m


def fuel_carbide(pu_frac: float, density: float = 12.3) -> openmc.Material:
    """(U,Pu)C; 12.3 g/cm3 ~ 90% of ~13.6 g/cm3 (approx.). Carbon as C-12 only (C-13, 1.1%, not in the library)."""
    m = openmc.Material(name=f"(U,Pu)C x={pu_frac:.3f}")
    _heavy_metal(m, pu_frac)
    m.add_nuclide("C12", 1.0, "ao")
    m.set_density("g/cm3", density)
    return m


def fuel_chloride(pu_frac: float, cl37: float = ENRICH["Cl37"], an_mol: float = 0.40,
                  density: float = 3.3) -> openmc.Material:
    """NaCl-(U,Pu)Cl3 with an_mol mole fraction of actinide trichloride; 3.3 g/cm3 at ~1,100 K (approx.,
    additive molar volumes from liquid NaCl ~1.5 and UCl3 ~4.8 g/cm3, both approx.)."""
    m = openmc.Material(name=f"NaCl-AnCl3 x={pu_frac:.3f} Cl37={cl37}")
    na, cl = 1 - an_mol, (1 - an_mol) + 3 * an_mol
    m.add_nuclide("Na23", na, "ao")
    _heavy_metal(m, pu_frac, per_hm=an_mol)
    m.add_nuclide("Cl37", cl * cl37, "ao")
    m.add_nuclide("Cl35", cl * (1 - cl37), "ao")
    m.set_density("g/cm3", density)
    return m


def lithium(li7: float = ENRICH["Li7"], density: float = 0.45) -> openmc.Material:
    """Liquid Li, 0.45 g/cm3 near 1,300-1,400 K (approx.)."""
    m = openmc.Material(name=f"Li (Li7={li7})")
    m.add_nuclide("Li7", li7, "ao")
    m.add_nuclide("Li6", 1 - li7, "ao")
    m.set_density("g/cm3", density)
    return m


def lead(density: float = 10.0) -> openmc.Material:
    """Liquid Pb, natural; ~10.0 g/cm3 near 1,150 K (approx., 11.37 - 1.19e-3 T)."""
    m = openmc.Material(name="Pb")
    m.add_element("Pb", 1.0, "ao")
    m.set_density("g/cm3", density)
    return m


def helium(P_MPa: float = 7.0, T_K: float = 1400.0) -> openmc.Material:
    m = openmc.Material(name="He")
    m.add_nuclide("He4", 1.0, "ao")
    rho = P_MPa * 1e6 * 4.0026e-3 / (8.314462618 * T_K) / 1000.0  # ideal gas, g/cm3 (calc)
    m.set_density("g/cm3", rho)
    return m


def nb1zr(density: float = 8.57) -> openmc.Material:
    m = openmc.Material(name="Nb-1Zr")
    m.add_nuclide("Nb93", 0.99, "wo")
    m.add_element("Zr", 0.01, "wo")
    m.set_density("g/cm3", density)
    return m


def molybdenum(density: float = 10.2) -> openmc.Material:
    m = openmc.Material(name="Mo")
    m.add_element("Mo", 1.0, "ao")
    m.set_density("g/cm3", density)
    return m


def tungsten(vector: dict | None = None, density: float = 19.3, name: str = "W nat") -> openmc.Material:
    m = openmc.Material(name=name)
    for n, f in (vector or W_NAT).items():
        m.add_nuclide(n, f, "ao")
    m.set_density("g/cm3", density)
    return m


def w_enriched(main: str, frac: float = 0.95) -> dict:
    """Isotope vector with `main` at `frac`, the rest in natural proportions (approx. enrichment)."""
    rest = {k: v for k, v in W_NAT.items() if k != main}
    s = sum(rest.values())
    out = {k: (1 - frac) * v / s for k, v in rest.items()}
    out[main] = frac
    return out


def sic(density: float = 2.9) -> openmc.Material:
    """SiC/SiC composite, 2.9 g/cm3 (~90% of 3.21, approx.). Carbon as C-12 only."""
    m = openmc.Material(name="SiC")
    m.add_element("Si", 1.0, "ao")
    m.add_nuclide("C12", 1.0, "ao")
    m.set_density("g/cm3", density)
    return m


def void() -> openmc.Material:
    m = openmc.Material(name="void")
    m.add_nuclide("He4", 1.0)
    m.set_density("g/cm3", 1e-9)
    return m


def cermet(pu_frac: float, matrix: openmc.Material, un_vol: float = 0.60, un_density: float = 13.5):
    """UN-matrix cermet as a single material (UN 60 vol% at 95% TD, approx.)."""
    return openmc.Material.mix_materials([fuel_nitride(pu_frac, un_density), matrix],
                                         [un_vol, 1 - un_vol], "vo")


# ---- extended screen ------------------------------------------------------------------------
EXTRA_SCORES = ["H3-production", "(n,p)", "(n,a)"]


def screen_plus(components, T: float, particles: int = 20000, batches: int = 60, inactive: int = 20,
                threads: int = 1, label: str = "case", seed: int = 1) -> dict:
    """Same model and definitions as infinite.screen(); also returns per-nuclide rates normalised per
    fission neutron produced (nu-fission = 1), tritium production and the coolant-relevant (n,p)/(n,a)."""
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
    scores = ["absorption", "fission", "(n,gamma)", "nu-fission"] + EXTRA_SCORES
    t_rates = openmc.Tally(name="rates")
    t_rates.nuclides = nuclides
    t_rates.scores = scores
    edges = np.logspace(-5, np.log10(2e7), 301)
    t_flux = openmc.Tally(name="spectrum")
    t_flux.filters = [openmc.EnergyFilter(edges)]
    t_flux.scores = ["flux"]
    settings = infinite._settings(T, particles, batches, inactive)
    settings.seed = seed
    model = openmc.Model(geom, openmc.Materials([mix]), settings, tallies=openmc.Tallies([t_rates, t_flux]))
    model.materials.cross_sections = str(infinite.XS)
    with tempfile.TemporaryDirectory() as tmp:
        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            sp_path = model.run(threads=threads, output=False)
            with openmc.StatePoint(sp_path) as sp:
                keff = sp.keff
                rates = sp.get_tally(name="rates")
                flux = sp.get_tally(name="spectrum").mean.ravel()
                smap = dict(zip(scores, rates.scores))  # OpenMC may normalise score names
                per = {n: {s: float(rates.get_values(nuclides=[n], scores=[smap[s]]).ravel()[0]) for s in scores}
                       for n in nuclides}
        finally:
            os.chdir(cwd)
    FIS, FER = infinite.FISSILE, infinite.FERTILE
    fissile_abs = sum(per[n]["absorption"] for n in FIS if n in per)
    fertile_cap = sum(per[n]["absorption"] - per[n]["fission"] for n in FER if n in per)
    total_abs = sum(v["absorption"] for v in per.values()) or 1.0
    nu_f = sum(v["nu-fission"] for v in per.values()) or 1.0
    fis = sum(v["fission"] for v in per.values()) or 1.0
    parasitic = {n: v["absorption"] / total_abs for n, v in per.items() if n not in FIS + FER}
    cdf = np.cumsum(flux) / flux.sum()
    median_E = float(edges[1:][np.searchsorted(cdf, 0.5)])
    # flux fractions by energy band
    def band(lo, hi):
        sel = (edges[1:] > lo) & (edges[:-1] < hi)
        return float(flux[sel].sum() / flux.sum())
    return {
        "label": label, "T_K": T, "k_inf": float(keff.nominal_value), "k_inf_sd": float(keff.std_dev),
        "conversion_ratio": fertile_cap / fissile_abs if fissile_abs else float("nan"),
        "median_energy_eV": median_E,
        "flux_fraction": {"<1keV": band(0, 1e3), "1-100keV": band(1e3, 1e5), ">100keV": band(1e5, 2e7)},
        "parasitic_absorption_share": dict(sorted(parasitic.items(), key=lambda kv: -kv[1])[:10]),
        "parasitic_total_share": float(sum(parasitic.values())),
        "tritium_per_fission": sum(v["H3-production"] for v in per.values()) / fis,
        "np_per_fission": {n: v["(n,p)"] / fis for n, v in per.items() if v["(n,p)"] / fis > 1e-4},
        "na_per_fission": {n: v["(n,a)"] / fis for n, v in per.items() if v["(n,a)"] / fis > 1e-4},
        "capture_per_fission": {n: v["(n,gamma)"] / fis for n, v in per.items() if v["(n,gamma)"] / fis > 1e-3},
        "temperature_note": "" if infinite.LIB_T[0] <= T <= infinite.LIB_T[1]
        else f"T outside library {infinite.LIB_T}; nearest temperature used",
        "particles": particles, "batches": batches, "inactive": inactive,
    }


def rho_pcm(k: float) -> float:
    return 1e5 * (k - 1) / k


def worth_pcm(k0, s0, k1, s1):
    w = rho_pcm(k1) - rho_pcm(k0)
    sd = 1e5 * np.hypot(s0 / k0**2, s1 / k1**2)
    return float(w), float(sd)

"""Shared material definitions for the new-geometry scoping (Phase 1).

All densities are approximate handbook-class values at operating temperature (labelled (approx.)
in the study page). Natural isotopic abundances come from the property database (nuclide table,
IAEA LiveChart); isotopes not in the OpenMC library (config/targets.yaml: openmc_library) are
dropped and the element renormalised, which is recorded in LIBRARY_NOTES.

Common assumptions (identical across all family analyses):
  Pu vector (approx., reactor-grade): Pu-238 2, Pu-239 60, Pu-240 24, Pu-241 9, Pu-242 5 atom %.
  Uranium: depleted, 0.25 % U-235.  N-15 99.9 %, B-11 99.9 %, Li-7 99.99 %, Cl-37 99 %.
"""
from __future__ import annotations

import sqlite3
from functools import lru_cache
from pathlib import Path

import openmc
import yaml

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "htfbr.sqlite"

PU_VECTOR = {"Pu238": 0.02, "Pu239": 0.60, "Pu240": 0.24, "Pu241": 0.09, "Pu242": 0.05}
U_VECTOR = {"U235": 0.0025, "U238": 0.9975}
N15_ENRICHMENT = 0.999

# Densities at operating temperature, g/cm3 (approx.)
RHO = {
    "UPu_liquid": 16.0,   # liquid U-Pu near 2,000 C (A2 assumption)
    "UPuN": 13.6,         # (U,Pu)N, ~95 % of ~14.3 theoretical
    "W": 19.0,            # ~19.3 at room temperature, less thermal expansion
    "Mo": 10.0,
    "AlN": 3.26,
    "Al_liquid": 2.15,    # ~1,300-1,500 C (A2 uses 2.10 at 1,500-1,800 C)
    "Pb_liquid": 9.3,     # 11441 - 1.2795 T[K] kg/m3 at ~1,670 K (approx. correlation)
    "He_7MPa": 0.0024,    # ideal gas, 7 MPa, ~1,400 K
    "ZrN": 7.09,
    "Al2O3": 3.95,
    "SiC": 3.21,
}

LIBRARY_NOTES: set[str] = set()


@lru_cache(None)
def _library_nuclides() -> frozenset:
    cfg = yaml.safe_load((ROOT / "config" / "targets.yaml").read_text())["openmc_library"]["nuclides"]
    return frozenset(f"{el}{a}" for g in cfg.values() for el, masses in g.items() for a in masses)


@lru_cache(None)
def natural(symbol: str) -> dict[str, float]:
    """Natural atom fractions from the database, restricted to library nuclides (renormalised)."""
    con = sqlite3.connect(DB)
    rows = con.execute("SELECT a, abundance_pct FROM nuclide WHERE symbol=? AND abundance_pct>0", (symbol,)).fetchall()
    con.close()
    allfr = {f"{symbol}{a}": p / 100 for a, p in rows}
    lib = _library_nuclides()
    kept = {k: v for k, v in allfr.items() if k in lib}
    missing = sum(v for k, v in allfr.items() if k not in lib)
    if missing > 1e-6:
        LIBRARY_NOTES.add(f"{symbol}: {', '.join(k for k in allfr if k not in lib)} not in library "
                          f"({100*missing:.3f} at% of natural {symbol}); remaining isotopes renormalised")
    s = sum(kept.values())
    return {k: v / s for k, v in kept.items()}


def _add_el(m: openmc.Material, symbol: str, atoms: float):
    for nuc, f in natural(symbol).items():
        m.add_nuclide(nuc, atoms * f)


def heavy_metal(m: openmc.Material, pu_frac: float, atoms: float = 1.0):
    for n, f in U_VECTOR.items():
        m.add_nuclide(n, atoms * (1 - pu_frac) * f)
    for n, f in PU_VECTOR.items():
        m.add_nuclide(n, atoms * pu_frac * f)


def upu_liquid(pu: float) -> openmc.Material:
    m = openmc.Material(name=f"liquid U-Pu {pu:.3f}")
    heavy_metal(m, pu)
    m.set_density("g/cm3", RHO["UPu_liquid"])
    return m


def upun(pu: float) -> openmc.Material:
    m = openmc.Material(name=f"(U,Pu)N-15 {pu:.3f}")
    heavy_metal(m, pu)
    m.add_nuclide("N15", N15_ENRICHMENT)
    m.add_nuclide("N14", 1 - N15_ENRICHMENT)
    m.set_density("g/cm3", RHO["UPuN"])
    return m


def element(symbol: str, rho: float) -> openmc.Material:
    m = openmc.Material(name=symbol)
    _add_el(m, symbol, 1.0)
    m.set_density("g/cm3", rho)
    return m


def W():
    return element("W", RHO["W"])


def Mo():
    return element("Mo", RHO["Mo"])


def Al():
    m = openmc.Material(name="Al liquid")
    m.add_nuclide("Al27", 1.0)
    m.set_density("g/cm3", RHO["Al_liquid"])
    return m


def Pb():
    return element("Pb", RHO["Pb_liquid"])


def He(rho: float = RHO["He_7MPa"]):
    m = openmc.Material(name="He")
    m.add_nuclide("He4", 1.0)
    m.set_density("g/cm3", rho)
    return m


def vacuum():
    """Vacuum gap: helium at 1e-9 g/cm3, as in analysis/common/infinite.py void_worth()."""
    return He(1e-9)


def AlN():
    m = openmc.Material(name="AlN (N-15)")
    m.add_nuclide("Al27", 1.0)
    m.add_nuclide("N15", N15_ENRICHMENT)
    m.add_nuclide("N14", 1 - N15_ENRICHMENT)
    m.set_density("g/cm3", RHO["AlN"])
    return m


def ZrN():
    m = openmc.Material(name="ZrN (N-15)")
    _add_el(m, "Zr", 1.0)
    m.add_nuclide("N15", N15_ENRICHMENT)
    m.add_nuclide("N14", 1 - N15_ENRICHMENT)
    m.set_density("g/cm3", RHO["ZrN"])
    return m


def Al2O3():
    m = openmc.Material(name="Al2O3")
    m.add_nuclide("Al27", 2.0)
    m.add_nuclide("O16", 3.0)   # O-17/O-18 not in library (0.24 at% of O): O-16 only
    LIBRARY_NOTES.add("O: O-16 only (O-17, O-18 not in library, 0.24 at% of natural O)")
    m.set_density("g/cm3", RHO["Al2O3"])
    return m


def SiC():
    m = openmc.Material(name="SiC")
    _add_el(m, "Si", 1.0)
    m.add_nuclide("C12", 1.0)   # C-13 not in library (1.1 at% of natural C)
    LIBRARY_NOTES.add("C: C-12 only (C-13 not in library, 1.1 at% of natural C)")
    m.set_density("g/cm3", RHO["SiC"])
    return m

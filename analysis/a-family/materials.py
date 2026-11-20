"""Material definitions for the Family A (aluminium-cooled) Phase 1 screen.

All densities are (approx.) values at temperature unless stated; they are listed in DENSITY so the
README and the docs can quote them. Isotopic vectors follow the common Phase 1 assumptions:

- Plutonium: approx. reactor-grade vector, atom %: Pu-238 2, Pu-239 60, Pu-240 24, Pu-241 9, Pu-242 5.
- Uranium: depleted, 0.25 at% U-235.
- Enriched isotopes at best achievable enrichment (P3): N-15 99.9%, B-11 99.9%.
"""
from __future__ import annotations

import openmc

PU_VECTOR = {"Pu238": 0.02, "Pu239": 0.60, "Pu240": 0.24, "Pu241": 0.09, "Pu242": 0.05}
U_VECTOR = {"U235": 0.0025, "U238": 0.9975}

# g/cm3 (approx.). Sources: general handbook knowledge unless noted; A2 page assumptions reused.
DENSITY = {
    "UPu_liquid": 16.0,     # A2 page assumption, liquid U-Pu at ~2,000 C
    "UPuN": 13.6,           # (U,Pu)N pellet, ~95% of ~14.3 theoretical (approx.)
    "Al_2100K": 2.10,       # A2 page assumption (1,500-1,800 C)
    "Al_1600K": 2.20,       # liquid Al at ~1,300 C (approx.)
    "W": 19.0,              # 19.25 at room T, ~1% lower hot (approx.)
    "AlN": 3.20,            # 3.26 at room T (approx.)
    "ZrB2": 6.00,           # 6.09 at room T (approx.)
    "Na": 0.80,             # hypothetical comparison; Na boils at 897 C (db)
    "Pb": 9.50,             # hypothetical comparison at A1/A2 temperatures (approx.)
}


def _heavy_metal(pu_frac: float) -> dict[str, float]:
    """Atom fractions of heavy-metal nuclides for Pu/(U+Pu) = pu_frac (atom basis)."""
    hm = {n: (1 - pu_frac) * f for n, f in U_VECTOR.items()}
    hm.update({n: pu_frac * f for n, f in PU_VECTOR.items()})
    return hm


def upu_liquid(pu_frac: float, density: float | None = None) -> openmc.Material:
    m = openmc.Material(name=f"U-Pu liquid {pu_frac:.3f}")
    for n, f in _heavy_metal(pu_frac).items():
        m.add_nuclide(n, f)
    m.set_density("g/cm3", density or DENSITY["UPu_liquid"])
    return m


def upu_nitride(pu_frac: float, n15: float = 0.999, density: float | None = None) -> openmc.Material:
    m = openmc.Material(name=f"(U,Pu)N {pu_frac:.3f} N15={n15}")
    for n, f in _heavy_metal(pu_frac).items():
        m.add_nuclide(n, f)
    m.add_nuclide("N15", n15)
    m.add_nuclide("N14", 1 - n15)
    m.set_density("g/cm3", density or DENSITY["UPuN"])
    return m


def aluminium(density: float) -> openmc.Material:
    m = openmc.Material(name="Al")
    m.add_nuclide("Al27", 1.0)
    m.set_density("g/cm3", density)
    return m


def sodium(density: float = DENSITY["Na"]) -> openmc.Material:
    m = openmc.Material(name="Na")
    m.add_nuclide("Na23", 1.0)
    m.set_density("g/cm3", density)
    return m


def lead(density: float = DENSITY["Pb"]) -> openmc.Material:
    m = openmc.Material(name="Pb")
    m.add_element("Pb", 1.0)
    m.set_density("g/cm3", density)
    return m


def tungsten(density: float = DENSITY["W"]) -> openmc.Material:
    m = openmc.Material(name="W")
    m.add_element("W", 1.0)
    m.set_density("g/cm3", density)
    return m


def aln(n15: float = 0.999, density: float = DENSITY["AlN"]) -> openmc.Material:
    m = openmc.Material(name=f"AlN N15={n15}")
    m.add_nuclide("Al27", 1.0)
    m.add_nuclide("N15", n15)
    m.add_nuclide("N14", 1 - n15)
    m.set_density("g/cm3", density)
    return m


def zrb2(b11: float = 0.999, density: float = DENSITY["ZrB2"]) -> openmc.Material:
    """b11: atom fraction B-11 in boron. Natural boron is 0.8035 B-11 (db, LiveChart)."""
    m = openmc.Material(name=f"ZrB2 B11={b11}")
    m.add_element("Zr", 1.0)
    m.add_nuclide("B11", 2 * b11)
    m.add_nuclide("B10", 2 * (1 - b11))
    m.set_density("g/cm3", density)
    return m


def al_u_pu_solution(x_hm: float, pu_frac: float, T_K: float = 2100.0, scale: float = 1.0) -> openmc.Material:
    """Liquid Al with dissolved U+Pu, heavy-metal atom fraction x_hm.

    Density from ideal mixing of molar volumes (approx.): liquid Al 27.0/2.10 = 12.85 cm3/mol,
    liquid U-Pu 238.6/16.0 = 14.9 cm3/mol at ~2,100 K. Al-U has a strongly negative mixing enthalpy,
    so the real liquid is probably somewhat denser; `scale` multiplies the density for sensitivity.
    """
    hm = _heavy_metal(pu_frac)
    m = openmc.Material(name=f"Al-U-Pu x_hm={x_hm:.3f} Pu={pu_frac:.3f}")
    m.add_nuclide("Al27", 1 - x_hm)
    for n, f in hm.items():
        m.add_nuclide(n, x_hm * f)
    M_hm = 238.6
    v_al, v_hm = 26.98 / DENSITY["Al_2100K"], M_hm / DENSITY["UPu_liquid"]
    rho = ((1 - x_hm) * 26.98 + x_hm * M_hm) / ((1 - x_hm) * v_al + x_hm * v_hm)
    m.set_density("g/cm3", rho * scale)
    return m


def solution_density(x_hm: float) -> tuple[float, float]:
    """(total density, heavy-metal density) in g/cm3 for the ideal-mixing solution model."""
    v_al, v_hm = 26.98 / DENSITY["Al_2100K"], 238.6 / DENSITY["UPu_liquid"]
    vol = (1 - x_hm) * v_al + x_hm * v_hm
    return ((1 - x_hm) * 26.98 + x_hm * 238.6) / vol, x_hm * 238.6 / vol


def void_filler() -> openmc.Material:
    """Same filler as analysis/common/infinite.void_worth: He-4 at 1e-9 g/cm3."""
    m = openmc.Material(name="void-filler")
    m.add_nuclide("He4", 1.0)
    m.set_density("g/cm3", 1e-9)
    return m

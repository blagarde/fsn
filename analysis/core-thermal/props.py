"""Thermophysical properties for the core nuclear-thermal model (chemistry deliberately ignored).

Where the property database has a value it is used: heat capacity of liquid Al, Pb, Na from
NIST-JANAF (`thermo` table) and boiling points at 1 bar (htfbr_data.thermo.boiling_point_K).
Everything else is a handbook correlation entered by hand and marked APPROX with its source;
these are E3-grade (literature, not yet ingested with a locator) and are listed in the study
page so they can be checked and moved into the database (open question in docs/open-questions.md).

All functions take T in kelvin and return SI units.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable

try:
    from htfbr_data import db as _db, thermo as _thermo
except ImportError:  # the model still runs without the database, on the fallbacks below
    _db = _thermo = None

R_GAS = 8.314462618


@lru_cache(None)
def _con():
    return _db.connect() if _db else None


@lru_cache(None)
def _janaf_cp(formula: str, molar_mass: float):
    """cp(T) in J/(kg K) from the JANAF condensed-phase table, or None."""
    con = _con()
    if con is None:
        return None
    sid = _thermo.find_species(con, formula, "cr,l") or _thermo.find_species(con, formula, "l")
    if sid is None:
        return None
    return lambda T: _thermo.interp(con, sid, "cp", T) / molar_mass


@lru_cache(None)
def boiling_K(formula: str, fallback: float) -> tuple[float, str]:
    con = _con()
    if con is not None:
        Tb, how = _thermo.boiling_point_K(con, formula)
        if Tb:
            return Tb, f"db: {how}"
    return fallback, "APPROX handbook"


# --------------------------------------------------------------------------- coolants
@dataclass
class Coolant:
    name: str
    kind: str                       # liquid_metal | gas | salt
    rho: Callable[[float], float]   # kg/m3
    cp: Callable[[float], float]    # J/(kg K)
    k: Callable[[float], float]     # W/(m K)
    mu: Callable[[float], float]    # Pa s
    T_melt: float                   # K
    T_boil: float                   # K at the stated pressure (gas: none)
    pressure_Pa: float
    sources: dict = field(default_factory=dict)


def _cp_or(formula, M, fallback):
    f = _janaf_cp(formula, M)
    if f is None:
        return (lambda T: fallback), f"APPROX constant {fallback} J/kg K"
    return f, "db: NIST-JANAF cp (liquid)"


def coolants() -> dict[str, Coolant]:
    out = {}
    cp, cps = _cp_or("Na", 0.022990, 1260.0)
    Tb, Tbs = boiling_K("Na", 1156.0)
    out["Na"] = Coolant(
        "sodium", "liquid_metal",
        rho=lambda T: 219 + 275.32 * (1 - T / 2503.7) + 511.58 * (1 - T / 2503.7) ** 0.5,
        cp=cp, k=lambda T: 124.67 - 0.11381 * T + 5.5226e-5 * T**2 - 1.1842e-8 * T**3,
        mu=lambda T: math.exp(-6.4406 - 0.3958 * math.log(T) + 556.835 / T),
        T_melt=371.0, T_boil=Tb, pressure_Pa=1e5,
        sources={"rho,k,mu": "APPROX Fink & Leibowitz 1995 (ANL/RE-95/2) correlations", "cp": cps, "T_boil": Tbs})
    cp, cps = _cp_or("Pb", 0.2072, 145.0)
    Tb, Tbs = boiling_K("Pb", 2016.0)
    out["Pb"] = Coolant(
        "lead", "liquid_metal",
        rho=lambda T: 11441 - 1.2795 * T, cp=cp, k=lambda T: 9.2 + 0.011 * T,
        mu=lambda T: 4.55e-4 * math.exp(1069 / T),
        T_melt=600.6, T_boil=Tb, pressure_Pa=1e5,
        sources={"rho,k,mu": "APPROX OECD/NEA Handbook on lead-bismuth eutectic and lead (2015) correlations",
                 "cp": cps, "T_boil": Tbs})
    cp, cps = _cp_or("Al", 0.026982, 1177.0)
    Tb, Tbs = boiling_K("Al", 2792.0)
    out["Al"] = Coolant(
        "aluminium", "liquid_metal",
        rho=lambda T: 2377.23 - 0.311 * (T - 933.47),
        cp=cp, k=lambda T: 85.0 + 0.0 * T,  # liquid Al ~ 85-100 W/m K near and above melting
        mu=lambda T: 1e-3 * 10 ** (-0.7324 + 803.49 / T),
        T_melt=933.5, T_boil=Tb, pressure_Pa=1e5,
        sources={"rho,mu": "APPROX Assael et al., J. Phys. Chem. Ref. Data 35 (2006) 285",
                 "k": "APPROX ~85 W/m K, liquid Al handbook range 85-100", "cp": cps, "T_boil": Tbs})

    def he(p_bar):
        return Coolant(
            f"helium {p_bar:.0f} bar", "gas",
            rho=lambda T: p_bar * 1e5 / (2077.1 * T), cp=lambda T: 5193.0,
            k=lambda T: 2.682e-3 * (1 + 1.123e-3 * p_bar) * T ** (0.71 * (1 - 2e-4 * p_bar)),
            mu=lambda T: 3.674e-7 * T**0.7, T_melt=0.0, T_boil=0.0, pressure_Pa=p_bar * 1e5,
            sources={"all": "APPROX KTA 3102.1 helium correlations; ideal gas"})
    out["He70"] = he(70.0)
    out["FLiBe"] = Coolant(
        "FLiBe (2LiF-BeF2)", "salt",
        rho=lambda T: 2413 - 0.488 * T, cp=lambda T: 2386.0, k=lambda T: 1.1,
        mu=lambda T: 1.16e-4 * math.exp(3755 / T), T_melt=732.0, T_boil=1703.0, pressure_Pa=1e5,
        sources={"all": "APPROX Romatoski & Hu, Ann. Nucl. Energy 109 (2017) 635 recommended values"})
    return out


# --------------------------------------------------------------------------- fuels and walls
@dataclass
class Solid:
    name: str
    rho: float                        # kg/m3 at temperature (approx.)
    cp: Callable[[float], float]      # J/(kg K)
    k: Callable[[float], float]       # W/(m K)
    T_limit: float                    # K: melting, solidus or dissociation (the hard limit)
    alpha_lin: float                  # 1/K linear thermal expansion (liquids: volumetric/3)
    liquid: bool = False
    sources: dict = field(default_factory=dict)


def _mox_k(T):
    t = T / 1000.0  # Fink 2000 (UO2, 95 % TD), used for MOX without the Pu correction
    return 100.0 / (7.5408 + 17.692 * t + 3.6142 * t * t) + 6400.0 / t**2.5 * math.exp(-16.35 / t)


def fuels() -> dict[str, Solid]:
    return {
        "UPu_liquid": Solid("liquid U-Pu", 16000.0, lambda T: 190.0, lambda T: 40.0, 3900.0, 2.0e-5, True,
                            {"all": "APPROX: k 30-50 W/m K and cp ~190 J/kg K (liquid U, IAEA 2008 thermophysical "
                                    "properties handbook range); limit = boiling (U ~4,400 K), Pu vapour sets a lower practical limit"}),
        "UPuZr": Solid("U-Pu-Zr metal (solid)", 15800.0, lambda T: 175.0, lambda T: 16.0 + 0.0145 * (T - 300.0),
                       1350.0, 1.7e-5, False,
                       {"all": "APPROX Kim & Hofman, J. Nucl. Mater. 2004 / Billone; limit = U-19Pu-10Zr solidus ~1,350 K"}),
        "UPuN": Solid("(U,Pu)N", 13600.0, lambda T: 200.0 + 0.03 * (T - 300.0), lambda T: 1.864 * T**0.361,
                      2300.0, 1.0e-5, False,
                      {"k": "APPROX Hayes et al., J. Nucl. Mater. 171 (1990) 300 (UN)",
                       "limit": "APPROX: practical limit set by dissociation and N2 pressure, ~2,300 K (melts ~3,100 K under N2)"}),
        "UPuO2": Solid("(U,Pu)O2", 10400.0, lambda T: 300.0 + 0.05 * (T - 300.0), _mox_k, 3000.0, 1.1e-5, False,
                       {"k": "APPROX Fink, J. Nucl. Mater. 279 (2000) 1 (UO2, 95 % TD)", "limit": "MOX solidus ~3,000 K"}),
    }


def walls() -> dict[str, Solid]:
    return {
        "W": Solid("tungsten", 19000.0, lambda T: 150.0, lambda T: 174.9 - 0.1067 * T + 5.0e-5 * T**2 - 7.8e-9 * T**3,
                   3695.0, 5.0e-6, sources={"k": "APPROX Touloukian-type fit, ~100 W/m K at 2,000 K"}),
        "Mo": Solid("molybdenum", 10000.0, lambda T: 300.0, lambda T: 150.0 - 0.03 * T, 2896.0, 6.0e-6,
                    sources={"all": "APPROX handbook"}),
        "SiC": Solid("silicon carbide", 3210.0, lambda T: 1200.0, lambda T: 30.0, 2800.0, 4.5e-6,
                     sources={"k": "APPROX irradiated CVD SiC ~20-40 W/m K"}),
        "steel": Solid("austenitic steel", 7600.0, lambda T: 600.0, lambda T: 25.0, 1650.0, 1.8e-5,
                       sources={"all": "APPROX handbook"}),
        "AlN": Solid("aluminium nitride", 3260.0, lambda T: 1200.0, lambda T: 30.0, 2700.0, 5.0e-6,
                     sources={"k": "APPROX ~30 W/m K at high temperature"}),
    }

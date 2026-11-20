"""Family X (liquid U-Pu at ~2,000 C): property-database facts used by the screening.

Pulls, read-only, from data/htfbr.sqlite (NIST-JANAF, SGTE unary, ENDF/B-VIII.0 averages):
vapour pressures and saturation temperatures of the carriers, Ca latent heat, liquid heat
capacities, CaF2 formation energy per mol F2, melting points, and per-isotope fast absorption.

Output: analysis/x-family/results/thermo_chem.json
Run:    export PATH=/opt/mamba/envs/nuc/bin:$PATH; python analysis/x-family/thermo_chem.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from htfbr_data import thermo  # noqa: E402

OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)
con = sqlite3.connect(f"file:{ROOT / 'data' / 'htfbr.sqlite'}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
C2K = 273.15


def vp(formula, T):
    v, note = thermo.vapor_pressure_bar(con, formula, T)
    return {"T_K": T, "T_C": round(T - C2K, 1), "p_bar": v, "note": note}


def t_sat(formula, p_bar, lo=1200.0, hi=3500.0):
    """Saturation temperature at pressure p_bar by bisection on vapor_pressure_bar."""
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if thermo.vapor_pressure_bar(con, formula, mid)[0] < p_bar:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def col(formula, phase, column, T):
    sid = thermo.find_species(con, formula, phase)
    return thermo.interp(con, sid, column, T) if sid else None


res = {"source": "data/htfbr.sqlite (read-only)", "vapour_pressure": {}, "saturation_T": {}}

# Vapour pressures of the carriers at fuel-relevant temperatures
for f in ("Pb", "Ca", "CaF2"):
    res["vapour_pressure"][f] = [vp(f, T + C2K) for T in (1500, 1800, 1900, 2000, 2100)]

# Ca saturation temperature vs pressure (X3 boiling column) and Pb
res["saturation_T"]["Ca"] = [{"p_bar": p, "T_C": round(t_sat("Ca", p) - C2K, 1)} for p in (1, 3, 5, 9.2, 12, 15, 20)]
res["saturation_T"]["Pb"] = [{"p_bar": p, "T_C": round(t_sat("Pb", p) - C2K, 1)} for p in (1, 3, 5)]

# Ca latent heat: dfH(Ca,g) - dfH(Ca,cr,l) at T (JANAF, kJ/mol); per kg with M = 40.078 g/mol
M_Ca = 40.078e-3
lat = []
for T in (1500.0, 1774.0, 2000.0):
    hg, hl = col("Ca", "g", "dfH", T), col("Ca", "cr,l", "dfH", T)
    # above Tb JANAF switches the element reference to the gas, so dfH(cr,l) becomes negative
    dh = (hg - hl) if (hg is not None and hl is not None) else None
    lat.append({"T_K": T, "dHvap_kJ_mol": dh, "dHvap_MJ_kg": dh / M_Ca / 1e3 if dh else None})
res["Ca_latent_heat"] = lat

# Liquid heat capacities (J/mol K -> kJ/kg K)
M = {"Ca": 40.078e-3, "Pb": 207.2e-3, "CaF2": 78.075e-3}
cps = {}
for f in M:
    for ph in ("cr,l", "l"):
        c = col(f, ph, "cp", 2000.0)
        if c:
            cps[f] = {"phase": ph, "cp_J_molK_2000K": c, "cp_kJ_kgK": c / M[f] / 1e3}
            break
res["cp_liquid_2000K"] = cps

# CaF2 stability per mol F2 (R1/R9 reference); U, Pu and W fluorides are not in JANAF here
res["CaF2_dfG_per_F2_kJ"] = {str(T): col("CaF2", "cr,l", "dfG", T) for T in (298.15, 1500.0, 2000.0)}
res["fluorides_missing_from_db"] = [s for s in ("UF3", "UF4", "PuF3", "WF6", "PbF2")
                                    if thermo.find_species(con, s, "cr") is None and thermo.find_species(con, s, "cr,l") is None]

# Melting points
mp = {}
for f in ("U", "Pu", "W", "Re", "Ca", "Pb", "CaF2"):
    v, note = thermo.melting_point_K(con, f)
    row = con.execute("SELECT value FROM property WHERE material=? AND quantity='melting_point'", (f,)).fetchone()
    mp[f] = {"janaf_K": v, "janaf_note": note, "sgte_K": row[0] if row else None}
res["melting_point"] = mp

# Per-isotope non-fission absorption, U-235 fission-spectrum average (mb)
iso = {}
for z, a, mt, v in con.execute(
        "SELECT z, a, mt, value_b FROM xs_avg WHERE z IN (9,20,74,82) AND weighting_id='watt_u235' AND mt IN (101,103,107)"):
    iso.setdefault(f"{z}-{a}", {})[{101: "abs", 103: "np", 107: "na"}[mt]] = round(v * 1e3, 2)
res["isotope_fast_absorption_mb"] = iso
nat = {}
for s, v in con.execute("SELECT symbol, value_b FROM v_xs_natural WHERE mt=101 AND weighting_id='watt_u235' AND symbol IN ('Ca','F','Pb','W','U')"):
    nat[s] = round(v * 1e3, 1)
res["natural_fast_absorption_mb"] = nat

(OUT / "thermo_chem.json").write_text(json.dumps(res, indent=1, default=str))
print(json.dumps({k: res[k] for k in ("saturation_T", "Ca_latent_heat", "cp_liquid_2000K", "CaF2_dfG_per_F2_kJ",
                                      "fluorides_missing_from_db", "melting_point")}, indent=1, default=str))
for f in res["vapour_pressure"]:
    print(f, [(d["T_C"], round(d["p_bar"], 4)) for d in res["vapour_pressure"][f]])

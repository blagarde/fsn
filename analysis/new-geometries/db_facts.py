"""Database facts used by the new-geometry scoping (read-only queries on data/htfbr.sqlite).

Writes results/db_facts.json: fast absorption (MT 101, U-235 fission-spectrum average) of the
boundary and coolant elements, SGTE/JANAF melting points, coolant vapour pressures, Al2O3 heat
capacity, and the AlN decomposition pressures that matter when AlN faces a vacuum gap (L7, S9).
"""
from __future__ import annotations

import json
import math
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from htfbr_data import thermo  # noqa: E402

con = sqlite3.connect(ROOT / "data" / "htfbr.sqlite")
con.row_factory = sqlite3.Row
out: dict = {"source": "data/htfbr.sqlite (read-only)"}

els = ["He", "C", "Pb", "Al", "Zr", "Si", "O", "Nb", "Mo", "W", "Ta", "Re", "N", "Y"]
out["fast_absorption_mb"] = {r["symbol"]: round(1000 * r["value_b"], 1) for r in con.execute(
    f"SELECT symbol, value_b FROM v_xs_natural WHERE mt=101 AND weighting_id='watt_u235' "
    f"AND symbol IN ({','.join('?'*len(els))})", els)}
out["fast_absorption_basis"] = "ENDF/B-VIII.0 via NJOY2016, natural abundance, MT 101, U-235 Watt spectrum average"

out["melting_point_C"] = {r["material"]: round(r["value_si"] - 273.15, 0) for r in con.execute(
    "SELECT material, value_si FROM property WHERE quantity='melting_point' AND material IN "
    "('W','Ta','Re','Mo','Nb','U','Pu','Zr','Al','Pb','Si')")}
out["melting_point_basis"] = "SGTE unary via pycalphad (property table)"
for f in ("Al2O3", "AlN"):
    T, note = thermo.melting_point_K(con, f)
    out.setdefault("melting_point_C_janaf", {})[f] = (round(T - 273.15, 0) if T else None, note)

vp = {}
for f in ("Al", "Pb"):
    for TC in (1000, 1200, 1300, 1400, 1500, 1600, 1700, 1800):
        p, note = thermo.vapor_pressure_bar(con, f, TC + 273.15)
        vp[f"{f}@{TC}C"] = (p, note)
out["vapour_pressure_bar"] = vp
for f in ("Al", "Pb"):
    T, note = thermo.boiling_point_K(con, f)
    out.setdefault("boiling_point_C", {})[f] = (round(T - 273.15, 0), note)

# Pb pressure needed for a 300 K boiling margin (taxonomy exclusion rule 1)
def pb_pressure_for_boiling(TbC):
    p, note = thermo.vapor_pressure_bar(con, "Pb", TbC + 273.15)
    return p, note
out["Pb_pressure_for_300K_margin_bar"] = {f"outlet {T} C": pb_pressure_for_boiling(T + 300)[0]
                                          for T in (1400, 1500, 1600, 1700)}

# Al2O3 heat capacity (particle carrier, S8)
sid = thermo.find_species(con, "Al2O3", "cr")
cps = {}
for TK in (1000, 1200, 1400, 1600):
    cp = thermo.interp(con, sid, "cp", TK)
    cps[TK] = cp
out["Al2O3_cp_J_per_molK"] = cps
out["Al2O3_cp_kJ_per_kgK"] = {k: round(v / 101.961, 3) for k, v in cps.items() if v}

# AlN decomposition (R4): AlN(cr) -> Al(l) + 1/2 N2 with Al liquid present (a_Al = 1),
# and congruent vaporisation into vacuum AlN(cr) -> Al(g) + 1/2 N2 with p_Al = 2 p_N2.
R = 8.314462618e-3
s_aln = thermo.find_species(con, "AlN", "cr")
s_alg = thermo.find_species(con, "Al", "g")
dec = {}
for TC in (1200, 1300, 1400, 1500, 1600, 1800, 2000):
    T = TC + 273.15
    g_aln = thermo.interp(con, s_aln, "dfG", T)
    g_alg = thermo.interp(con, s_alg, "dfG", T)
    if g_aln is None or g_alg is None:
        dec[TC] = None
        continue
    pN2_with_Al_liquid = math.exp(2 * g_aln / (R * T))
    K = math.exp(-(g_alg - g_aln) / (R * T))  # p_Al * p_N2^0.5
    pN2_vac = (K / 2) ** (2 / 3)
    dec[TC] = {"dfG_AlN_kJ": g_aln, "pN2_over_AlN+Al(l)_bar": pN2_with_Al_liquid,
               "vacuum_congruent_pAl_bar": 2 * pN2_vac, "vacuum_congruent_pN2_bar": pN2_vac}
out["AlN_decomposition"] = dec
out["AlN_decomposition_basis"] = "NIST-JANAF dfG of AlN(cr) and Al(g); reference states Al(cr,l), N2(g)"

(Path(__file__).parent / "results" / "db_facts.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))

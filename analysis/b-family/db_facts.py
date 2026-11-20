"""Pull every database fact the B-family screening uses -> results/db_facts.json (read-only queries).

Sources: NIST-JANAF (thermo), SGTE unary melting points (property), ENDF/B-VIII.0 spectrum averages
(xs_avg, v_xs_natural), IAEA LiveChart (nuclide).
"""
from __future__ import annotations

import json
import sqlite3

from htfbr_data import thermo
from htfbr_data.chem import parse_formula
from bfam import HERE, ROOT

con = sqlite3.connect(f"file:{ROOT / 'data' / 'htfbr.sqlite'}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
out: dict = {}


def dfG(formula, phase, T):
    sid = thermo.find_species(con, formula, phase)
    return None if sid is None else thermo.interp(con, sid, "dfG", T)


# --- phase window of coolants and salts (JANAF) ---
out["phase"] = {}
for f in ("Li", "Pb", "ClNa", "Mo", "W"):
    mp, mb = thermo.melting_point_K(con, f)
    bp, bb = thermo.boiling_point_K(con, f)
    out["phase"][f] = {"melting_K": mp, "melting_basis": mb, "boiling_K": bp, "boiling_basis": bb}
out["sgte_melting_K"] = {r["material"]: r["value"] for r in con.execute(
    "SELECT material, value FROM property WHERE quantity='melting_point'")}

out["vapour_pressure_bar"] = {}
for f, Ts in {"Li": [1200, 1300, 1400, 1500, 1600], "Pb": [1100, 1200, 1300, 1400, 1500],
              "ClNa": [1000, 1100, 1200, 1300, 1400]}.items():
    out["vapour_pressure_bar"][f] = {T: thermo.vapor_pressure_bar(con, f, T) for T in Ts}

# --- heat capacity of coolants (J/kg K), JANAF cp / molar mass ---
M = {"Li": 6.94, "Pb": 207.2, "ClNa": 58.44}
out["cp_J_per_kgK"] = {}
for f, Ts in {"Li": [1000, 1300, 1500], "Pb": [800, 1100, 1300], "ClNa": [1100, 1200]}.items():
    sid = thermo.find_species(con, f, "cr,l")
    out["cp_J_per_kgK"][f] = {T: thermo.interp(con, sid, "cp", T) / M[f] * 1000 for T in Ts}

# --- R1: generalised Ellingham, kJ per mol of reactant ---
def per_reactant(formula, phase, T, el, n_el_per_reactant):
    g = dfG(formula, phase, T)
    if g is None:
        return None
    n = parse_formula(formula)[el]
    return g / (n / n_el_per_reactant)

out["R1_nitrides_kJ_per_mol_N2"] = {T: {f: per_reactant(f, "cr", T, "N", 2) for f in
                                        ("NZr", "NTi", "N4Si3", "AlN", "BN")} for T in (1200, 1500, 1800)}
out["R1_oxides_kJ_per_mol_O2"] = {T: {f: per_reactant(f, "cr", T, "O", 2) for f in
                                      ("Li2O", "O2Zr", "O2Si", "Al2O3", "MgO", "O2Ti", "CaO")} for T in (1000, 1300, 1500)}
out["R1_carbides_kJ_per_mol_C"] = {T: {f: per_reactant(f, "cr", T, "C", 1) for f in
                                       ("CSi", "CZr", "CTi", "CB4")} for T in (1200, 1500, 1800)}
out["R9_NaCl_kJ_per_mol_Cl2"] = {T: per_reactant("ClNa", "cr,l", T, "Cl", 2) for T in (1000, 1100, 1200, 1300)}
out["missing_species"] = {f: thermo.find_species(con, f, "cr") is None and thermo.find_species(con, f, "cr,l") is None
                          for f in ("NU", "CU", "Cl3U", "Cl3Pu", "Cl2Mo", "Cl2Ni", "Cl2Cr", "Cl2Fe", "Mo2N",
                                    "NNb", "ONb", "O2Nb", "OPb", "Li3N", "He")}

# --- cross sections (mb), U-235 fission-spectrum (watt) and resonance integral ---
q = """SELECT symbol, mt, weighting_id, value_b FROM v_xs_natural WHERE mt IN (101,103,107)
       AND weighting_id IN ('watt_u235','ri_1overE') AND symbol IN ('Li','Pb','N','Cl','Na','W','Mo','Nb','Si','C','Zr','Re','Ta')"""
out["xs_natural_mb"] = {}
for r in con.execute(q):
    out["xs_natural_mb"].setdefault(r["symbol"], {})[f"{r['weighting_id']}_mt{r['mt']}"] = 1000 * r["value_b"]
q = """SELECT n.symbol||'-'||x.a AS iso, x.mt, x.weighting_id, x.value_b FROM xs_avg x JOIN nuclide n USING(z,a)
       WHERE x.mt IN (101,103,105,107) AND x.weighting_id IN ('watt_u235','ri_1overE')
       AND n.symbol||'-'||x.a IN ('Li-6','Li-7','N-14','N-15','Cl-35','Cl-37','W-182','W-183','W-184','W-186',
       'Mo-92','Mo-95','Mo-98','Mo-100','Pb-204','Pb-206','Pb-207','Pb-208')"""
out["xs_isotope_mb"] = {}
for r in con.execute(q):
    out["xs_isotope_mb"].setdefault(r["iso"], {})[f"{r['weighting_id']}_mt{r['mt']}"] = 1000 * r["value_b"]

# --- activation and transmutation product half-lives ---
out["half_lives"] = {f"{r['symbol']}-{r['a']}": r["half_life_text"] for r in con.execute(
    """SELECT symbol, a, half_life_text FROM nuclide WHERE (symbol,a) IN (VALUES ('H',3),('C',14),('Cl',36),
    ('S',35),('Ar',37),('W',181),('W',185),('W',187),('Mo',93),('Mo',99),('Po',210),('Pb',209),('Na',24),
    ('Nb',94),('Nb',92),('Ta',182),('Li',8),('Si',31),('N',16))""")}
out["abundance_pct"] = {f"{r['symbol']}-{r['a']}": r["abundance_pct"] for r in con.execute(
    "SELECT symbol, a, abundance_pct FROM nuclide WHERE symbol IN ('Li','N','Cl','W','Mo','Pb') AND abundance_pct>0")}

(HERE / "results" / "db_facts.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps({k: out[k] for k in ("phase", "vapour_pressure_bar", "cp_J_per_kgK", "R1_nitrides_kJ_per_mol_N2",
                                      "R1_oxides_kJ_per_mol_O2", "R1_carbides_kJ_per_mol_C", "R9_NaCl_kJ_per_mol_Cl2",
                                      "missing_species", "half_lives")}, indent=1, default=str))

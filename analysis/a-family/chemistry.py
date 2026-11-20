"""Family A chemistry checks from NIST-JANAF (db) and COST 507 CALPHAD (db file, pycalphad).

Outputs results/chemistry.json. Everything here is thermodynamics only (evidence level E3, or E3/E4
where JANAF and CALPHAD are mixed); kinetics, irradiation and fission products are not covered.

Checks
  J1  Nitride stability per mol N2 (AlN, ZrN, TiN, BN) and AlN dissociation pressure p_N2(AlN/Al).
  J2  Nitriding of diboride walls: MB2 + 3/2 N2 -> MN + 2 BN and MB2 + 1/2 N2 -> MN + 2 B.
      Threshold p_N2 compared with p_N2 set by AlN/Al (nitrogen-saturated aluminium).
  J3  Al2O vapour over Al(l) + Al2O3: 4 Al(l) + Al2O3 -> 3 Al2O(g).
  J4  Oxide stability per mol O2 at temperature (Al2O3 vs ZrO2, CaO).
  C1  COST 507: N solubility in liquid Al saturated with AlN.
  C2  COST 507: Ti and B in liquid Al saturated with TiB2 (TiB2 wall alternative).
  C3  COST 507 + JANAF: Zr and B in liquid Al saturated with ZrB2. COST 507 has no ZrB2 phase, so a
      stoichiometric ZRB2 phase is added with G = GHSERZR + 2 GHSERBB + dfG_JANAF(T) (linear fit,
      1500-2500 K). The B-Zr liquid interaction is not assessed in COST 507 (taken as ideal).
  C4  COST 507: Zr in liquid Al saturated with Al3Zr (upper bound if Zr activity were ~1).
"""
from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path

import numpy as np

from htfbr_data import thermo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DB = ROOT / "data" / "htfbr.sqlite"
R = 8.314462618e-3  # kJ/mol/K
TS = [1600.0, 1900.0, 2100.0, 2300.0]


def dfG(con, formula, phase, T):
    sid = thermo.find_species(con, formula, phase)
    return thermo.interp(con, sid, "dfG", T)


def janaf_checks(con) -> dict:
    out = {"T_K": TS, "per_mol_N2_kJ": {}, "per_mol_O2_kJ": {}, "p_N2_AlN_bar": [], "diboride_nitriding": {},
           "p_Al2O_bar": []}
    for name, f, n in (("AlN", "AlN", 1), ("ZrN", "NZr", 1), ("TiN", "NTi", 1), ("BN", "BN", 1)):
        out["per_mol_N2_kJ"][name] = [2 / n * dfG(con, f, "cr", T) for T in TS]
    for T in TS:
        g = dfG(con, "AlN", "cr", T)
        out["p_N2_AlN_bar"].append(math.exp(2 * g / (R * T)))
    for mb2, mn, label in (("B2Zr", "NZr", "ZrB2"), ("B2Ti", "NTi", "TiB2")):
        rows = []
        for T, pAlN in zip(TS, out["p_N2_AlN_bar"]):
            g_mb2, g_mn, g_bn = dfG(con, mb2, "cr", T), dfG(con, mn, "cr", T), dfG(con, "BN", "cr", T)
            d1 = g_mn + 2 * g_bn - g_mb2          # per 1.5 mol N2
            d2 = g_mn - g_mb2                     # per 0.5 mol N2 (B left as element)
            p1 = math.exp(d1 / (1.5 * R * T))
            p2 = math.exp(d2 / (0.5 * R * T))
            rows.append({"T_K": T, "dG_to_MN_2BN_kJ": d1, "p_N2_threshold_MN_2BN_bar": p1,
                         "dG_to_MN_2B_kJ": d2, "p_N2_threshold_MN_2B_bar": p2,
                         "p_N2_AlN_over_threshold": pAlN / p1})
        out["diboride_nitriding"][label] = rows
    for T in TS:
        d = 3 * dfG(con, "Al2O", "g", T) - dfG(con, "Al2O3", "cr,l", T)
        out["p_Al2O_bar"].append(math.exp(-d / (3 * R * T)))
    for name, f, nO in (("Al2O3", "Al2O3", 3), ("ZrO2", "O2Zr", 2), ("CaO", "CaO", 1)):
        ph = "cr,l" if name == "Al2O3" else "cr"
        out["per_mol_O2_kJ"][name] = [dfG(con, f, ph, T) * 2 / nO for T in TS]
    # ZrB2 dfG fit for C3
    Tfit = np.arange(1500.0, 2501.0, 100.0)
    g = [dfG(con, "B2Zr", "cr", T) for T in Tfit]
    a, b = np.polyfit(Tfit, np.array(g) * 1000.0, 1)  # J/mol = b*T + a ... polyfit returns slope first
    out["ZrB2_dfG_fit_J"] = {"A": float(b), "B": float(a), "form": "dfG = A + B*T, 1500-2500 K"}
    out["ZrB2_dfG_kJ"] = [dfG(con, "B2Zr", "cr", T) for T in TS]
    out["TiB2_dfG_kJ"] = [dfG(con, "B2Ti", "cr", T) for T in TS]
    return out


def calphad_checks(con, zrb2_fit) -> dict:
    from pycalphad import Database, equilibrium, variables as v
    path = con.execute("SELECT a.local_path FROM calphad_db d JOIN artifact a USING(artifact_id) "
                       "WHERE d.db_id='cost507'").fetchone()[0]
    text = Path(path).read_text(errors="replace")
    out = {"database": "cost507 (" + Path(path).name + ")"}
    dbf = Database(text)

    def eq(dbx, comps, phases, conds):
        r = equilibrium(dbx, comps, phases, conds, verbose=False)
        return r

    def liquid_x(r, el):
        ph = r.Phase.values.squeeze()
        x = r.X.sel(component=el).values.squeeze()
        npv = r.NP.values.squeeze()
        for i, p in enumerate(ph):
            if p == "LIQUID":
                return float(x[i])
        return float("nan")

    def phases_present(r):
        return [str(p) for p in r.Phase.values.squeeze() if str(p)]

    # C0 cross-check of reference states: AlN dfG from cost507 vs JANAF
    from pycalphad import calculate
    c0 = []
    for T in TS:
        ga = float(calculate(dbf, ["AL", "N", "VA"], "ALN", T=T, P=101325, N=1).GM.values.ravel()[0]) * 2
        gl = float(calculate(dbf, ["AL"], "LIQUID", T=T, P=101325, N=1).GM.values.ravel()[0])
        gn = float(dbf.symbols["GHSERNN"].subs({v.T: T, v.P: 101325}))
        c0.append({"T_K": T, "dfG_AlN_cost507_kJ": (ga - gl - gn) / 1000, "dfG_AlN_janaf_kJ": dfG(con, "AlN", "cr", T)})
    out["C0_AlN_crosscheck"] = c0

    # C1 Al-N: overall x_N = 0.01 (AlN-saturated if solubility is lower)
    c1 = []
    for T in TS:
        r = eq(dbf, ["AL", "N", "VA"], ["LIQUID", "ALN"], {v.X("N"): 0.01, v.T: T, v.P: 101325, v.N: 1})
        c1.append({"T_K": T, "x_N_liquid": liquid_x(r, "N"), "phases": phases_present(r)})
    out["C1_N_in_Al_sat_AlN"] = c1

    # C2 Al-B-Ti with TiB2: overall 2 at% Ti, 4 at% B
    c2 = []
    ph = [p for p in dbf.phases if p in ("LIQUID", "B2TI", "ALB2", "ALB12_ALPHA", "ALB12_BETA", "AL3M_DO22",
                                         "FCC_A1", "BCC_A2", "HCP_A3")]
    for T in TS:
        r = eq(dbf, ["AL", "B", "TI", "VA"], ph, {v.X("TI"): 0.02, v.X("B"): 0.04, v.T: T, v.P: 101325, v.N: 1})
        c2.append({"T_K": T, "x_Ti_liquid": liquid_x(r, "TI"), "x_B_liquid": liquid_x(r, "B"),
                   "phases": phases_present(r)})
    out["C2_TiB2_in_Al"] = c2

    # C3 Al-B-Zr with an added ZrB2 phase (JANAF)
    A, B = zrb2_fit["A"], zrb2_fit["B"]
    add = (f"\n PHASE ZRB2JANAF % 2 1 2 !\n CONSTITUENT ZRB2JANAF :ZR:B: !\n"
           f" PARAMETER G(ZRB2JANAF,ZR:B;0) 298.15 GHSERZR#+2*GHSERBB#+{A:.1f}{B:+.4f}*T; 6000 N !\n")
    dbz = Database(text + add)
    ph = [p for p in dbz.phases if p in ("LIQUID", "ZRB2JANAF", "ALB2", "ALB12_ALPHA", "ALB12_BETA", "AL3ZR1",
                                         "AL2ZR1", "FCC_A1", "BCC_A2", "HCP_A3")]
    c3 = []
    for T in TS:
        r = eq(dbz, ["AL", "B", "ZR", "VA"], ph, {v.X("ZR"): 0.02, v.X("B"): 0.04, v.T: T, v.P: 101325, v.N: 1})
        c3.append({"T_K": T, "x_Zr_liquid": liquid_x(r, "ZR"), "x_B_liquid": liquid_x(r, "B"),
                   "phases": phases_present(r)})
    out["C3_ZrB2_in_Al"] = c3
    out["C3_note"] = ("ZrB2 added from JANAF (GHSER reference states: hcp Zr, beta-B; reference-state error "
                      "of a few kJ/mol, approx.); B-Zr liquid interaction not assessed in cost507 (ideal).")

    # C5 Al-N-Zr with an added ZrN phase (JANAF): is ZrN a candidate Al-facing layer?
    Tf = np.arange(1500.0, 2501.0, 100.0)
    gz = [dfG(con, "NZr", "cr", T) * 1000.0 for T in Tf]
    bz, az = np.polyfit(Tf, gz, 1)
    addn = (f"\n PHASE ZRNJANAF % 2 1 1 !\n CONSTITUENT ZRNJANAF :ZR:N: !\n"
            f" PARAMETER G(ZRNJANAF,ZR:N;0) 298.15 GHSERZR#+GHSERNN#+{az:.1f}{bz:+.4f}*T; 6000 N !\n")
    dbn = Database(text + addn)
    ph = [p for p in dbn.phases if p in ("LIQUID", "ZRNJANAF", "ALN", "AL3ZR1", "AL2ZR1", "FCC_A1", "HCP_A3", "BCC_A2")]
    c5 = []
    for T in TS:
        r = eq(dbn, ["AL", "N", "ZR", "VA"], ph, {v.X("ZR"): 0.02, v.X("N"): 0.02, v.T: T, v.P: 101325, v.N: 1})
        c5.append({"T_K": T, "x_Zr_liquid": liquid_x(r, "ZR"), "x_N_liquid": liquid_x(r, "N"),
                   "phases": phases_present(r)})
    out["C5_ZrN_in_Al"] = c5
    out["C5_note"] = "ZrN added from JANAF (GHSERNN reference: N2 gas per 1/2 mol); N-Zr liquid not assessed (ideal)."

    # C4 Al-Zr: liquid in equilibrium with Al3Zr
    ph = [p for p in dbf.phases if p.startswith("AL") and "ZR" in p] + ["LIQUID", "FCC_A1", "HCP_A3", "BCC_A2"]
    c4 = []
    for T in TS:
        r = eq(dbf, ["AL", "ZR", "VA"], ph, {v.X("ZR"): 0.05, v.T: T, v.P: 101325, v.N: 1})
        c4.append({"T_K": T, "x_Zr_liquid": liquid_x(r, "ZR"), "phases": phases_present(r)})
    out["C4_Zr_in_Al_vs_Al3Zr"] = c4
    return out


def mass_transfer(c: dict) -> dict:
    """M1: diffusion-limited dissolution upper bound for wall materials in a non-isothermal Al loop (approx.).

    Hot wall at T_hot, bulk Al held at the saturation level of the cold leg (cold leg acts as a sink).
    k_m from Dittus-Boelter-type Sh = 0.023 Re^0.8 Sc^0.33 in a 10 mm tube at 3 m/s (A2 reference),
    liquid Al 2,100 kg/m3, 0.6 mPa s (A2 page assumptions), solute diffusivity 5e-9 m2/s (approx.).
    Interface reaction kinetics are ignored, so real rates may be far lower: this is a ceiling that shows
    whether solubility alone could matter, not a corrosion prediction.
    """
    rho, mu, D, d, u = 2100.0, 0.6e-3, 5e-9, 0.010, 3.0
    Re, Sc = rho * u * d / mu, mu / (rho * D)
    km = 0.023 * Re ** 0.8 * Sc ** 0.33 * D / d
    T = np.array(TS)
    cases = {
        "ZrB2 (Zr-limited)": ([r["x_Zr_liquid"] for r in c["C3_ZrB2_in_Al"]], 91.22, 0.813, 6000.0),
        "TiB2 (Ti-limited)": ([r["x_Ti_liquid"] for r in c["C2_TiB2_in_Al"]], 47.87, 0.689, 4500.0),
        "AlN (N-limited)": ([r["x_N_liquid"] for r in c["C1_N_in_Al_sat_AlN"]], 14.007, 0.342, 3200.0),
    }
    out = {"k_m_m_per_s": km, "Re": Re, "Sc": Sc, "assumptions": mass_transfer.__doc__.strip(), "rows": []}
    for T_hot, T_cold in ((2050.0, 1475.0), (1850.0, 1475.0), (1600.0, 1300.0)):
        for name, (xs, Mi, wfrac, rho_w) in cases.items():
            lx = np.log(np.array(xs))
            x_h = float(np.exp(np.interp(T_hot, T, lx, left=None)))
            x_c = float(np.exp(np.polyval(np.polyfit(1 / T, lx, 1), 1 / T_cold)))  # van't Hoff extrapolation
            dc = (x_h - x_c) * Mi / 26.98 * rho  # kg solute per m3 Al (dilute)
            J = km * dc
            rec = J / wfrac / rho_w * 3.156e7 * 1e3  # mm per year
            out["rows"].append({"material": name, "T_hot_K": T_hot, "T_cold_K": T_cold, "x_sat_hot": x_h,
                                "x_sat_cold": x_c, "flux_kg_m2_s": J, "recession_ceiling_mm_per_year": rec})
    return out


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    j = janaf_checks(con)
    try:
        c = calphad_checks(con, j["ZrB2_dfG_fit_J"])
    except Exception as e:  # keep the JANAF part if pycalphad fails
        c = {"error": repr(e)}
    out = {"janaf": j, "calphad": c}
    if "error" not in c:
        out["mass_transfer"] = mass_transfer(c)
    (HERE / "results" / "chemistry.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

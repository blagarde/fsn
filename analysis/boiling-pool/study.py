"""Boiling-fuel ("pressure cooker") study: thermal analysis and 1 GWth sizing. Writes results/thermal.json.

Run: /opt/mamba/envs/nuc/bin/python study.py
"""
import json
import math
from pathlib import Path

import model as M

OUT = Path(__file__).resolve().parent / "results"
P_TARGET = 1.0e9
C = 273.15


def options(T):
    """(label, liquid, vapour) for each boiling system at T."""
    out = []
    for x in (0.3, 0.5):
        out.append((f"NaCl-(U,Pu)Cl3, NaCl {x:.0%}", M.chloride_fuel(T, x), M.vapour("NaCl", T, x)))
    out.append(("7LiF-(U,Pu)F4, LiF 60%", M.fluoride_fuel(T, 0.6), M.vapour("LiF", T, 0.6)))
    for met in ("Pb", "Ca", "Mg"):
        out.append((f"U-Pu pool under boiling {met}", M.metal_carrier(met, T), M.vapour(met, T)))
    return out


# U-Pu metal itself (no database data): APPROX handbook values. Pu: Tb 3,501 K, dHvap 333 kJ/mol;
# U: Tb 4,404 K. Vapour over U-rich U-Pu is mostly Pu (Raoult on Pu).
def upu_vapour(T, x_pu=0.15):
    p = math.exp(-333e3 / M.R * (1 / T - 1 / 3501.0)) * x_pu   # bar
    rho_g = p * 1e5 * 0.2391 / (M.R * T)
    return {"P_Pa": p * 1e5, "rho_g": rho_g, "h_fg": 333e3 / 0.2391, "M_mean": 0.2391,
            "source": "APPROX handbook (Pu Tb 3,501 K, dHvap 333 kJ/mol), Raoult on Pu"}


def main():
    OUT.mkdir(exist_ok=True)
    res = {"solvents": [], "power_density": [], "architectures": {}, "walls": [], "skull": {}}

    # 1. what boils, at what pressure, and how much heat a cubic metre of vapour carries
    for T in (1800.0, 2000.0, 2200.0):
        for label, liq, vap in options(T):
            res["solvents"].append({"T_K": T, "option": label, "P_bar": vap["P_Pa"] / 1e5, "rho_g": vap["rho_g"],
                                    "h_fg_MJ_kg": vap["h_fg"] / 1e6, "rho_g_hfg_MJ_m3": vap["rho_g"] * vap["h_fg"] / 1e6,
                                    "rho_l": liq.rho, "flooding_MW_m2_D0.05": M.flooding_q(0.05, liq, vap) / 1e6,
                                    "flooding_MW_m2_D1": M.flooding_q(1.0, liq, vap) / 1e6})
    for T in (3200.0, 3500.0, 3800.0):
        v = upu_vapour(T)
        res["solvents"].append({"T_K": T, "option": "U-Pu metal itself (Pu boils)", "P_bar": v["P_Pa"] / 1e5,
                                "rho_g": v["rho_g"], "h_fg_MJ_kg": v["h_fg"] / 1e6,
                                "rho_g_hfg_MJ_m3": v["rho_g"] * v["h_fg"] / 1e6})

    # 2. power density a boiling pool can carry as vapour, at a given mean void (T = 2,000 K)
    T = 2000.0
    for label, liq, vap in options(T):
        for H in (0.3, 1.0, 2.0):
            row = {"option": label, "H_m": H}
            for a in (0.1, 0.3, 0.5):
                row[f"q3_MW_m3_at_void_{a}"] = M.q3_for_void(a, H, liq, vap) / 1e6
            row["fuel_m3_per_GW_at_void_0.3"] = P_TARGET / (row["q3_MW_m3_at_void_0.3"] * 1e6)
            res["power_density"].append(row)

    # 3. vessel walls: largest heat flux per material (chloride, NaCl 30 %, T_sat 2,000 K, P from vapour)
    liq, vap = M.chloride_fuel(T, 0.3), M.vapour("NaCl", T, 0.3)
    for r in (0.025, 0.25, 1.5):
        for name, mat in M.MATERIALS.items():
            for barrier in ("TiB2", "AlN"):
                for T_al in (1300.0, 1500.0):
                    # fuel-side surface sits below T_sat by the condensation drop (iterate once)
                    q_guess = 1e6
                    for _ in range(3):
                        h_c = M.condensation_h(liq, vap, 1.0, 50.0)
                        T_hot = T - q_guess / h_c
                        mf = M.max_flux(T_hot, max(vap["P_Pa"], 1e5) * 1.5, r, mat, barrier, 1e-3, 5e4, T_al)
                        q_guess = max(mf["q2_max"], 1e4)
                    res["walls"].append({"r_m": r, "material": name, "barrier": barrier, "T_al_bulk_K": T_al,
                                         "q2_max_MW_m2": mf["q2_max"] / 1e6,
                                         "t_struct_mm": (mf["t_struct"] or 0) * 1e3, "limits": mf["limits"],
                                         "T_hot_K": T_hot, "h_cond": h_c,
                                         "wall": {k: v for k, v in (mf.get("wall") or {}).items()}})

    # 4. architectures for 1 GWth (chloride, NaCl 30 %, 2,000 K, W-25Re + TiB2, Al at 1,500 K)
    best = max((w for w in res["walls"] if w["material"] == "W-25Re" and w["barrier"] == "TiB2"
                and w["T_al_bulk_K"] == 1500.0), key=lambda w: w["r_m"])  # r = 1.5 m
    def wall_q(r):
        return max(w["q2_max_MW_m2"] for w in res["walls"]
                   if w["r_m"] == r and w["material"] == "W-25Re" and w["barrier"] == "TiB2" and w["T_al_bulk_K"] == 1500.0) * 1e6
    arch = {}
    # (a) one vessel, cooled on its outside only
    for R in (1.0, 1.5, 2.5):
        H_pool, H_cond = 2 * R, 1.0
        A_wall = 2 * math.pi * R * (H_pool + H_cond) + 2 * math.pi * R * R
        q_w = wall_q(1.5)
        V = math.pi * R * R * H_pool
        P_wall = A_wall * q_w
        P_flood = M.flooding_q(2 * R, liq, vap) * math.pi * R * R
        P_void = M.q3_for_void(0.3, H_pool, liq, vap) * V
        arch[f"single vessel R {R} m"] = {"units": 1, "P_unit_MW": min(P_wall, P_flood, P_void) / 1e6,
            "limits_MW": {"wall": P_wall / 1e6, "flooding": P_flood / 1e6, "void 30%": P_void / 1e6},
            "fuel_m3": V, "wall_area_m2": A_wall}
    # (b) many small sealed boiling vessels ("pins") immersed in flowing Al
    for r, Hp in ((0.025, 1.0), (0.05, 1.0), (0.05, 0.3)):
        A_wall = 2 * math.pi * r * (Hp + 1.0)
        V = math.pi * r * r * Hp
        P_wall = A_wall * wall_q(0.025)
        P_flood = M.flooding_q(2 * r, liq, vap) * math.pi * r * r
        P_void = M.q3_for_void(0.3, Hp, liq, vap) * V
        Pu = min(P_wall, P_flood, P_void)
        n = P_TARGET / Pu
        arch[f"boiling pins r {r*100:.1f} cm, pool {Hp} m"] = {"units": n, "P_unit_kW": Pu / 1e3,
            "limits_kW": {"wall": P_wall / 1e3, "flooding": P_flood / 1e3, "void 30%": P_void / 1e3},
            "fuel_m3": n * V, "wall_area_m2": n * A_wall}
    # (c) one boiler vessel, vapour piped to Al-cooled condensers outside the core (no flooding limit at the
    #     pool; entrainment and void remain)
    for Hp in (0.3, 0.6, 1.0):
        q3 = M.q3_for_void(0.3, Hp, liq, vap)
        V = P_TARGET / q3
        D = math.sqrt(4 * V / (math.pi * Hp))
        arch[f"boiler + external condensers, pool depth {Hp} m"] = {"units": 1, "fuel_m3": V, "pool_diameter_m": D,
            "q3_MW_m3": q3 / 1e6, "vapour_m3_s": P_TARGET / (vap["rho_g"] * vap["h_fg"])}
    res["architectures"]["chloride_2000K"] = arch

    # 5. skull-cooled U-Pu metal boiling at ~3,500 K inside an Al-cooled vessel
    sk = []
    T_m, k_s, k_l = 1380.0, 30.0, 45.0   # APPROX: U-rich U-Pu solidus ~1,350-1,400 K; solid and liquid k
    for q2 in (1e6, 3e6, 10e6):
        for T_wall_in in (1000.0, 1200.0):
            delta = k_s * (T_m - T_wall_in) / q2
            sk.append({"q2_MW_m2": q2 / 1e6, "T_wall_inner_K": T_wall_in, "skull_mm": delta * 1e3,
                       "liquid_dT_needed_h": (3500.0 - T_m) / (q2 / 1e4)})  # h needed for liquid->skull, W/m2K at 1e4 scale
    res["skull"]["layers"] = sk
    mat = M.MATERIALS["Mo-TZM"]
    res["skull"]["wall"] = [dict(T_hot=Ti, **{k: v for k, v in M.max_flux(Ti, 2e5, 1.5, mat, "TiB2", 1e-3, 5e4, Tal).items() if k != "wall"})
                            for Ti in (1100.0, 1250.0) for Tal in (900.0 + 50, 1050.0)]
    v = upu_vapour(3500.0)
    liq_u = M.Liquid("U-Pu liquid", 15000.0, 1.5, 4e-3, 45.0, "APPROX")
    res["skull"]["void_power_density"] = {f"H {H} m": M.q3_for_void(0.3, H, liq_u, v) / 1e6 for H in (0.3, 1.0)}
    (OUT / "thermal.json").write_text(json.dumps(res, indent=1, default=str))

    # printed summary
    print("== what boils (P, vapour density, latent heat, heat per m3 of vapour, flooding per m2)")
    for s in res["solvents"]:
        if s["T_K"] in (2000.0, 3500.0):
            print(f"  {s['option']:34s} {s['T_K']:.0f} K: P {s['P_bar']:.3g} bar, rho_g {s['rho_g']:.3g}, h_fg {s['h_fg_MJ_kg']:.2f} MJ/kg, "
                  f"{s['rho_g_hfg_MJ_m3']:.2f} MJ/m3" + (f", flooding {s['flooding_MW_m2_D1']:.0f} MW/m2 (D 1 m)" if 'flooding_MW_m2_D1' in s else ""))
    print("== power density a boiling pool carries as vapour at mean void 0.3 (2,000 K)")
    for p in res["power_density"]:
        print(f"  {p['option']:34s} H {p['H_m']} m: {p['q3_MW_m3_at_void_0.3']:.3g} MW/m3 -> {p['fuel_m3_per_GW_at_void_0.3']:.0f} m3 per GW")
    print("== wall heat flux limits (chloride 2,000 K, Al 1,500 K, TiB2 barrier)")
    for w in res["walls"]:
        if w["barrier"] == "TiB2" and w["T_al_bulk_K"] == 1500.0:
            print(f"  r {w['r_m']} m {w['material']:8s}: {w['q2_max_MW_m2']:.2f} MW/m2, metal {w['t_struct_mm']:.1f} mm, limit: {w['limits']}")
    print("== architectures for 1 GWth")
    for k, a in arch.items():
        print(" ", k, {kk: (round(vv, 2) if isinstance(vv, float) else vv) for kk, vv in a.items()})
    print("== skull-cooled U-Pu", res["skull"]["void_power_density"])
    for s in res["skull"]["wall"]:
        print("  ", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items()})


if __name__ == "__main__":
    main()

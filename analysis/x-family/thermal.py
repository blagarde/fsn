"""Family X: 1D thermal sizing and power-cycle limits for X1 (Pb in W tubes), X2 (CaF2 direct
contact) and X3 (boiling Ca direct contact). Reference power 1,000 MWth, peak fuel 2,100 C.

All inputs not from the database are approximate and listed in PROPS / per-design dicts.
Database inputs (results/thermo_chem.json, from thermo_chem.py): Pb, Ca, CaF2 liquid cp at 2,000 K;
Ca vapour pressure (saturation curve) and latent heat; CaF2 melting point.

Output: analysis/x-family/results/thermal.json
Run:    python analysis/x-family/thermal.py   (after thermo_chem.py)
"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).parent
DB = json.loads((HERE / "results" / "thermo_chem.json").read_text())
g, R, C2K = 9.81, 8.314, 273.15
P_TH = 1.0e9          # W, reference thermal power (same as A2 for comparability)
T_FUEL_MAX = 2100.0   # C, peak fuel temperature limit (same as A2)
PEAK = 1.3            # local-to-average heat flux / power density

# Approximate properties (approx.) unless tagged db
PROPS = {
    "fuel": {"rho": 16400.0, "k": 40.0, "cp": 200.0, "mu": 4.0e-3, "sigma": 1.5,
             "note": "liquid U-Pu at ~2,000 C (approx.): rho 16.4 g/cm3, k 40 W/mK (30-50), cp 0.20 kJ/kgK, mu 4 mPa s, surface tension 1.5 N/m"},
    "Pb": {"rho": 8900.0, "k": 25.0, "cp": DB["cp_liquid_2000K"]["Pb"]["cp_kJ_kgK"] * 1e3, "mu": 0.8e-3,
           "note": "Pb at 1,250-1,800 C: rho 8.9 g/cm3, k 25 W/mK, mu 0.8 mPa s (approx.); cp from JANAF at 2,000 K (db)"},
    "W": {"k": 100.0, "note": "W at ~2,000 C: k 100 W/mK (approx.)"},
    "CaF2": {"rho": 2400.0, "k": 1.5, "cp": DB["cp_liquid_2000K"]["CaF2"]["cp_kJ_kgK"] * 1e3, "mu": 3.0e-3,
             "sigma_int": 1.2, "T_melt_C": DB["melting_point"]["CaF2"]["janaf_K"] - C2K,
             "note": "liquid CaF2: rho 2.4 g/cm3, k 1.5 W/mK, mu 3 mPa s, U/CaF2 interfacial tension 1.2 N/m (approx.); cp and melting point JANAF (db)"},
    "Ca": {"rho": 1200.0, "cp": DB["cp_liquid_2000K"]["Ca"]["cp_kJ_kgK"] * 1e3, "M": 40.078e-3,
           "note": "liquid Ca rho 1.2 g/cm3 (approx.); cp, vapour pressure and latent heat JANAF (db); vapour ideal gas"},
}


# ---------------------------------------------------------------- X1: Pb in W tubes in a fuel pool
def x1_case(q_avg, d_i=0.012, t_w=0.0015, p_over_do=1.6, T_in=1250.0, v=2.5, T_out=None):
    """Triangular tube bundle in a stationary fuel pool. Returns geometry, fractions, temperatures.
    If T_out is None, find the highest Pb outlet that keeps peak fuel <= T_FUEL_MAX."""
    f, pb, w = PROPS["fuel"], PROPS["Pb"], PROPS["W"]
    d_o = d_i + 2 * t_w
    p = p_over_do * d_o
    A_cell = math.sqrt(3) / 2 * p ** 2
    fr_pb = math.pi * d_i ** 2 / 4 / A_cell
    fr_w = math.pi * (d_o ** 2 - d_i ** 2) / 4 / A_cell
    fr_f = 1 - fr_pb - fr_w
    r_o, r_i, r_c = d_o / 2, d_i / 2, math.sqrt(A_cell / math.pi)

    def temps(T_out):
        m = P_TH / (pb["cp"] * (T_out - T_in))
        n = m / (pb["rho"] * v * math.pi * d_i ** 2 / 4)
        A_o = P_TH / q_avg
        H = A_o / (n * math.pi * d_o)
        V_core = n * A_cell * H
        q3 = P_TH / (fr_f * V_core)                     # W/m3 of fuel
        Re = pb["rho"] * v * d_i / pb["mu"]
        Pe = Re * pb["mu"] * pb["cp"] / pb["k"]
        h = (4.82 + 0.0185 * Pe ** 0.827) * pb["k"] / d_i
        ql = PEAK * q_avg
        dT_film = ql * (d_o / d_i) / h
        dT_wall = ql * r_o * math.log(r_o / r_i) / w["k"]
        dT_fuel = PEAK * q3 * r_c ** 2 / (4 * f["k"]) * (2 * math.log(r_c / r_o) - 1 + (r_o / r_c) ** 2)
        fric = 0.316 * Re ** -0.25
        dp = fric * H / d_i * pb["rho"] * v ** 2 / 2 + 1.5 * pb["rho"] * v ** 2 / 2
        pump = dp * m / pb["rho"] / 0.8
        # Pb loop at 5 bar (T_sat 2,108 C, db: >= 300 K boiling margin); fuel cover gas 1 bar plus head
        dp_wall = max(abs(5e5 - 1e5), abs(5e5 - 1e5 - f["rho"] * g * H))
        hoop_hydro = dp_wall / 1e6 * r_o / t_w  # MPa, thin-wall hoop stress at the worst height
        return dict(T_out_C=T_out, m_kg_s=m, n_tubes=n, H_m=H, V_core_m3=V_core, D_core_m=math.sqrt(4 * V_core / H / math.pi),
                    fuel_t=fr_f * V_core * f["rho"] / 1e3, q3_fuel_MW_m3=q3 / 1e6, P_density_core_MW_m3=P_TH / V_core / 1e6,
                    h_W_m2K=h, dT_film=dT_film, dT_wall=dT_wall, dT_fuel=dT_fuel,
                    T_wall_fuel_side_max_C=T_out + dT_film + dT_wall,
                    T_fuel_peak_C=T_out + dT_film + dT_wall + dT_fuel, dp_core_kPa=dp / 1e3, pump_kW=pump / 1e3,
                    hoop_stress_hydrostatic_MPa=hoop_hydro)

    if T_out is None:
        lo, hi = T_in + 50, T_FUEL_MAX
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            (lo, hi) = (mid, hi) if temps(mid)["T_fuel_peak_C"] < T_FUEL_MAX else (lo, mid)
        T_out = lo
    r = temps(T_out)
    r.update(q_avg_MW_m2=q_avg / 1e6, d_i_mm=d_i * 1e3, t_w_mm=t_w * 1e3, pitch_mm=p * 1e3, p_over_do=p_over_do,
             v_m_s=v, T_in_C=T_in, frac_fuel=fr_f, frac_Pb=fr_pb, frac_W=fr_w)
    return r


# ---------------------------------------------------------------- X2: CaF2 droplets rising through fuel
def terminal_velocity(d, rho_d, rho_c, mu_c, sigma):
    """min(rigid-sphere Schiller-Naumann, Mendelson wave analogy for deformable drops)."""
    v = 0.1
    for _ in range(200):
        Re = rho_c * v * d / mu_c
        cd = 24 / Re * (1 + 0.15 * Re ** 0.687) if Re < 1000 else 0.44
        v = math.sqrt(4 * g * d * (rho_c - rho_d) / (3 * cd * rho_c))
    v_mend = math.sqrt(2 * sigma / (rho_c * d) + g * d * (rho_c - rho_d) / (2 * rho_c))
    return min(v, v_mend), v, v_mend


def holdup_from_j(j, vt, n=2.0):
    """Richardson-Zaki dispersed-phase holdup with stationary continuous phase: j = vt*a*(1-a)^(n-1)."""
    lo, hi = 0.0, 1.0 / n  # branch below flooding
    if j >= vt * hi * (1 - hi) ** (n - 1):
        return float("nan")
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        (lo, hi) = (mid, hi) if vt * mid * (1 - mid) ** (n - 1) < j else (lo, mid)
    return lo


def x2():
    f, s = PROPS["fuel"], PROPS["CaF2"]
    T_in = s["T_melt_C"] + 50          # keep the salt liquid with 50 K margin
    approach = 30.0                    # K, droplet outlet below local fuel temperature (approx.)
    T_fuel_bulk = T_FUEL_MAX - 50      # stirred pool: bulk fuel 50 K below peak (approx.)
    T_out = T_fuel_bulk - approach
    dT = T_out - T_in
    drops = []
    for d_mm in (2, 3, 5, 8, 12):
        d = d_mm / 1e3
        vt, v_rigid, v_mend = terminal_velocity(d, s["rho"], f["rho"], f["mu"], s["sigma_int"])
        a_th = s["k"] / (s["rho"] * s["cp"])
        tau = (d / 2) ** 2 / (math.pi ** 2 * a_th)
        drops.append(dict(d_mm=d_mm, v_t_m_s=vt, v_rigid=v_rigid, v_mendelson=v_mend, tau_heat_s=tau,
                          height_to_equilibrate_m=3 * tau * vt))
    vt = [x for x in drops if x["d_mm"] == 5][0]["v_t_m_s"]
    rows = []
    for alpha in (0.05, 0.10, 0.15, 0.20, 0.30, 0.40):
        j = vt * alpha * (1 - alpha)
        qA = j * s["rho"] * s["cp"] * dT
        A = P_TH / qA
        H = 1.5
        rows.append(dict(holdup=alpha, j_m_s=j, q_per_area_MW_m2=qA / 1e6, area_m2_for_1GW=A, D_m=math.sqrt(4 * A / math.pi),
                         H_pool_m=H, pool_power_density_MW_m3=qA / H / 1e6, fuel_t=A * H * (1 - alpha) * f["rho"] / 1e3))
    m = P_TH / (s["cp"] * dT)
    return dict(T_in_C=T_in, T_out_C=T_out, dT_K=dT, mass_flow_kg_s=m, vol_flow_m3_s=m / s["rho"],
                flooding_j_max_m_s=vt * 0.25, droplets=drops, holdup_table=rows,
                fuel_fines_settling_mm_s={str(dd): (f["rho"] - s["rho"]) * g * (dd * 1e-6) ** 2 / (18 * s["mu"]) * 1e3 for dd in (10, 20, 50, 100)},
                assumptions="droplet outlet 30 K below bulk fuel; bulk fuel 50 K below 2,100 C peak; 5 mm drops; Richardson-Zaki n=2; pool height 1.5 m (approx.)")


# ---------------------------------------------------------------- X3: boiling Ca
def p_sat_Ca(T_C):
    pts = DB["vapour_pressure"]["Ca"]
    # log-linear interpolation in 1/T of the db points
    xs = [1 / (p["T_K"]) for p in pts]
    ys = [math.log(p["p_bar"]) for p in pts]
    x = 1 / (T_C + C2K)
    for i in range(len(xs) - 1):
        if xs[i + 1] <= x <= xs[i]:
            return math.exp(ys[i] + (ys[i + 1] - ys[i]) * (x - xs[i]) / (xs[i + 1] - xs[i]))
    i = 0 if x > xs[0] else len(xs) - 2
    return math.exp(ys[i] + (ys[i + 1] - ys[i]) * (x - xs[i]) / (xs[i + 1] - xs[i]))


def T_sat_Ca(p_bar):
    lo, hi = 1300.0, 2400.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        (lo, hi) = (mid, hi) if p_sat_Ca(mid) < p_bar else (lo, mid)
    return lo


def x3():
    f, c = PROPS["fuel"], PROPS["Ca"]
    h_fg = [x for x in DB["Ca_latent_heat"] if x["T_K"] == 2000.0][0]["dHvap_MJ_kg"] * 1e6
    T_in = 1250.0  # liquid Ca inlet, above fuel solidus ~1,130 C (approx.) and Ca melting 842 C (db)
    out = []
    for p_top in (5.0, 9.2, 12.0):
        T_sat = T_sat_Ca(p_top)
        q_kg = c["cp"] * (T_sat - T_in) + h_fg
        m = P_TH / q_kg
        rho_v = p_top * 1e5 * c["M"] / (R * (T_sat + C2K))
        Qv = m / rho_v
        # depth at which T_sat reaches the 2,100 C fuel limit (no boiling below it)
        p_lim = p_sat_Ca(T_FUEL_MAX)
        depth_boil = (p_lim - p_top) * 1e5 / (f["rho"] * g)
        vgj = 1.53 * (f["sigma"] * g * (f["rho"] - rho_v) / f["rho"] ** 2) ** 0.25
        C0 = 1.2
        rows = []
        for alpha in (0.1, 0.2, 0.3, 0.5):
            jg = alpha * vgj / (1 - C0 * alpha)  # Zuber-Findlay with stationary liquid: a = jg/(C0 jg + vgj)
            qA = jg * rho_v * q_kg
            rows.append(dict(void_top=alpha, j_g_m_s=jg, q_per_area_MW_m2=qA / 1e6, area_m2_for_1GW=P_TH / qA,
                             D_m=math.sqrt(4 * P_TH / qA / math.pi)))
        out.append(dict(p_top_bar=p_top, T_sat_C=T_sat, h_fg_MJ_kg=h_fg / 1e6, heat_per_kg_MJ=q_kg / 1e6, m_kg_s=m,
                        rho_vapour_kg_m3=rho_v, vapour_flow_m3_s=Qv, depth_where_Tsat_reaches_2100C_m=depth_boil,
                        v_gj_m_s=vgj, j_g_if_core_D2m=Qv / (math.pi), void_table=rows))
    return dict(T_in_C=T_in, cases=out,
                assumptions="Zuber-Findlay drift flux C0=1.2, v_gj=1.53(sigma g drho/rho_l^2)^0.25 with U surface tension 1.5 N/m (approx.); Ca vapour ideal gas; h_fg JANAF at 2,000 K (db)")


# ---------------------------------------------------------------- power cycle
def cycle(T_out_C, T_sink_C=30.0, TIT_C=1450.0):
    Th, Tc = T_out_C + C2K, T_sink_C + C2K
    carnot = 1 - Tc / Th
    ca = 1 - math.sqrt(Tc / Th)
    # Realistic: closed Brayton (He, gamma 5/3) heated to min(TIT, T_out - 100 K), eta_c 0.88, eta_t 0.92,
    # compressor inlet 40 C, no recuperator, exhaust heat to a Rankine bottoming cycle (eta 0.35 of recovered
    # heat, 85% recovered), 5% pressure loss on the expansion, 3% auxiliaries/generator. Pressure ratio
    # optimised for combined efficiency. (approx.) Bottoming Rankine 0.35 of recovered heat.
    T3 = min(TIT_C, T_out_C - 100) + C2K
    T1, gam, ec, et = 313.15, 5 / 3, 0.88, 0.92
    best = None
    for pr10 in range(15, 120):
        pr = pr10 / 10
        x = pr ** ((gam - 1) / gam)
        T2 = T1 * (1 + (x - 1) / ec)
        xt = (0.95 * pr) ** ((gam - 1) / gam)
        T4 = T3 * (1 - et * (1 - 1 / xt))
        wnet = (T3 - T4) - (T2 - T1)
        qin = T3 - T2
        eb = wnet / qin
        eb *= 0.97
        ecc = eb + (1 - eb) * 0.35 * 0.85
        if best is None or ecc > best[0]:
            best = (ecc, eb, pr, T4 - C2K)
    return dict(T_out_C=T_out_C, carnot=carnot, curzon_ahlborn=ca, turbine_inlet_C=T3 - C2K,
                brayton_alone=best[1], combined_cycle=best[0], pressure_ratio=best[2], brayton_exhaust_C=best[3])


if __name__ == "__main__":
    res = {"props": {k: v["note"] for k, v in PROPS.items()}, "P_th_MW": P_TH / 1e6, "T_fuel_max_C": T_FUEL_MAX}
    x1 = []
    for q in (1e6, 2e6, 3e6, 4e6):
        for pod in (1.4, 1.6, 2.0):
            x1.append(x1_case(q, p_over_do=pod))
    res["X1"] = {"sweep": x1, "reference": x1_case(2e6, p_over_do=1.6),
                 "assumptions": "1,000 MWth; Pb inlet 1,250 C; 12 mm bore, 1.5 mm W wall, triangular pitch; Pb 2.5 m/s; "
                                "Nu = 4.82 + 0.0185 Pe^0.827; fuel conduction only (annular cell); peaking 1.3 applied at the hot end"}
    res["X2"] = x2()
    res["X3"] = x3()
    ref_out = {"X1": res["X1"]["reference"]["T_out_C"], "X2": res["X2"]["T_out_C"],
               "X3": [c for c in res["X3"]["cases"] if c["p_top_bar"] == 9.2][0]["T_sat_C"]}
    res["cycle"] = {k: cycle(v) for k, v in ref_out.items()}
    (HERE / "results" / "thermal.json").write_text(json.dumps(res, indent=1))

    print("X1 sweep: q MW/m2, p/d, T_out, fuel, Pb, W, n, H, D, fuel t, dTfilm/wall/fuel, pump kW, hoop MPa")
    for r in x1:
        print(f" {r['q_avg_MW_m2']:.0f} {r['p_over_do']:.1f} {r['T_out_C']:.0f}  {r['frac_fuel']:.2f} {r['frac_Pb']:.2f} {r['frac_W']:.3f}"
              f"  n={r['n_tubes']:.0f} H={r['H_m']:.2f} D={r['D_core_m']:.2f} {r['fuel_t']:.0f}t  {r['dT_film']:.0f}/{r['dT_wall']:.0f}/{r['dT_fuel']:.0f}"
              f"  {r['pump_kW']:.0f} kW  {r['hoop_stress_hydrostatic_MPa']:.1f}")
    x = res["X2"]
    print(f"X2: T_in {x['T_in_C']:.0f} T_out {x['T_out_C']:.0f} m {x['mass_flow_kg_s']:.0f} kg/s Q {x['vol_flow_m3_s']:.2f} m3/s j_flood {x['flooding_j_max_m_s']:.3f}")
    for d in x["droplets"]:
        print("  drop", {k: round(v, 3) for k, v in d.items()})
    for r in x["holdup_table"]:
        print("  ", {k: round(v, 3) for k, v in r.items()})
    print("  fines settling mm/s:", {k: round(v, 3) for k, v in x["fuel_fines_settling_mm_s"].items()})
    for c in res["X3"]["cases"]:
        print("X3", {k: round(v, 3) for k, v in c.items() if not isinstance(v, list)})
        for r in c["void_table"]:
            print("   ", {k: round(v, 3) for k, v in r.items()})
    for k, v in res["cycle"].items():
        print(k, {a: round(b, 3) for a, b in v.items()})

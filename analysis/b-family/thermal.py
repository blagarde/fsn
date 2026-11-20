"""1D thermal sizing and power-cycle limits for B1-B6 -> results/thermal.json, results/cycle.json.

Single average channel plus a hot channel (enthalpy-rise factor F_dH = 1.25, peak heat-flux factor
F_q = 1.5, both approx.), peak flux overlaid on the hot-channel outlet (conservative). Coolant cp
from JANAF (db) where available; other properties are (approx.) literature correlations noted inline.
"""
from __future__ import annotations

import json
import math
import sqlite3

import numpy as np
from htfbr_data import thermo

from bfam import HERE, ROOT

con = sqlite3.connect(f"file:{ROOT / 'data' / 'htfbr.sqlite'}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
R = 8.314462618
F_DH, F_Q = 1.25, 1.5           # hot-channel factors (approx.)
T_SINK = 303.15                 # 30 C
K0 = 273.15


def cp_db(formula, M_g, T):
    sid = thermo.find_species(con, formula, "cr,l")
    return thermo.interp(con, sid, "cp", T) / M_g * 1000.0


def tb_at_pressure(formula, p_bar):
    """Temperature where the JANAF (Clausius-Clapeyron above Tb) vapour pressure equals p_bar."""
    lo, hi = 800.0, 3500.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        p, _ = thermo.vapor_pressure_bar(con, formula, mid)
        if p is None or p > p_bar:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def h_vap_kJ(formula, T):
    g = thermo.find_species(con, formula, "g")
    c = thermo.find_species(con, formula, "cr,l")
    return thermo.enthalpy(con, g, T) - thermo.enthalpy(con, c, T)


# ---- coolant property sets (T in K) ----
def props(coolant, T, P_MPa=7.0):
    if coolant == "Li":   # rho, k, mu approx. (Li handbook-type correlations); cp db
        return dict(rho=562.0 - 0.10 * T, k=55.0, mu=2.4e-4, cp=cp_db("Li", 6.94, T), src="cp db JANAF; rho,k,mu approx.")
    if coolant == "Pb":   # OECD/NEA LBE-Pb handbook correlations (approx.)
        return dict(rho=11367.0 - 1.1944 * T, k=9.2 + 0.011 * T, mu=4.55e-4 * math.exp(1069.0 / T),
                    cp=cp_db("Pb", 207.2, min(T, 1300.0)), src="cp db JANAF; rho,k,mu approx. (NEA handbook form)")
    if coolant == "He":   # ideal gas (calc); KTA-type k and mu correlations (approx.)
        Pb = P_MPa * 10.0
        return dict(rho=P_MPa * 1e6 * 4.0026e-3 / (R * T), cp=2.5 * R / 4.0026e-3,
                    k=2.682e-3 * (1 + 1.123e-3 * Pb) * T ** (0.71 * (1 - 2e-4 * Pb)), mu=3.674e-7 * T ** 0.7,
                    src="rho, cp ideal gas (calc); k, mu approx. (KTA-type)")
    if coolant == "salt":  # NaCl-(U,Pu)Cl3, all approx. (no MSTDB access)
        return dict(rho=3300.0, cp=600.0, k=0.6, mu=4e-3, src="all approx.")
    raise KeyError(coolant)


def nusselt(coolant, Re, Pr):
    Pe = Re * Pr
    if coolant in ("Li", "Pb"):
        return 7.0 + 0.025 * Pe ** 0.8           # Lyon-type liquid-metal correlation (approx.)
    return 0.023 * Re ** 0.8 * Pr ** 0.4         # Dittus-Boelter


def darcy_f(Re):
    return 0.316 * Re ** -0.25 if Re < 1e5 else 0.184 * Re ** -0.2


def pin_core(name, P_MW, coolant, T_in_C, T_out_C, q_lin_avg, r_f, gap, t_clad, k_fuel, k_clad, h_gap,
             p_over_d, H=1.0, pump_eff=0.75, P_MPa=None, loop_factor=2.0):
    """Hexagonal pin lattice; returns temperatures (C), flux, velocity, pressure drop and pumping."""
    r_o = r_f + gap + t_clad
    d = 2 * r_o
    p = p_over_d * d
    A_cell = math.sqrt(3) / 2 * p * p
    A_flow = A_cell - math.pi * r_o ** 2
    Dh = 4 * A_flow / (2 * math.pi * r_o)
    n_pins = P_MW * 1e6 / (q_lin_avg * H)
    T_in, T_out = T_in_C + K0, T_out_C + K0
    Tm = 0.5 * (T_in + T_out)
    pr = props(coolant, Tm, P_MPa or 0.1)
    mdot = P_MW * 1e6 / (pr["cp"] * (T_out - T_in))
    G = mdot / (n_pins * A_flow)
    v = G / pr["rho"]
    Re = G * Dh / pr["mu"]
    Pr = pr["mu"] * pr["cp"] / pr["k"]
    h = nusselt(coolant, Re, Pr) * pr["k"] / Dh
    q_lin_pk = F_Q * q_lin_avg
    q_flux_pk = q_lin_pk / (2 * math.pi * r_o)
    T_hot_out = T_in + F_DH * (T_out - T_in)
    dT_film = q_flux_pk / h
    dT_clad = q_lin_pk * math.log(r_o / (r_f + gap)) / (2 * math.pi * k_clad)
    dT_gap = q_lin_pk / (2 * math.pi * (r_f + gap / 2) * h_gap)
    dT_fuel = q_lin_pk / (4 * math.pi * k_fuel)
    T_clad_out = T_hot_out + dT_film + dT_clad
    T_fuel_max = T_clad_out + dT_gap + dT_fuel
    dP_core = darcy_f(Re) * H / Dh * pr["rho"] * v * v / 2
    dP_loop = loop_factor * dP_core
    pump = dP_loop * mdot / pr["rho"] / pump_eff
    area = n_pins * A_cell
    return {
        "design": name, "P_MWth": P_MW, "coolant": coolant, "T_in_C": T_in_C, "T_out_C": T_out_C,
        "geometry": {"r_fuel_mm": r_f * 1e3, "gap_mm": gap * 1e3, "t_clad_mm": t_clad * 1e3, "p_over_d": p_over_d,
                     "H_m": H, "n_pins": round(n_pins), "core_diameter_m": math.sqrt(4 * area / math.pi),
                     "vol_frac_fuel": math.pi * r_f ** 2 / A_cell,
                     "vol_frac_clad": math.pi * (r_o ** 2 - (r_f + gap) ** 2) / A_cell,
                     "vol_frac_coolant": A_flow / A_cell, "Dh_mm": Dh * 1e3},
        "q_lin_avg_kW_m": q_lin_avg / 1e3, "q_lin_peak_kW_m": q_lin_pk / 1e3,
        "heat_flux_peak_MW_m2": q_flux_pk / 1e6,
        "core_power_density_MW_m3": P_MW / (area * H),
        "coolant": {**{k: v for k, v in pr.items()}, "mdot_kg_s": mdot, "velocity_m_s": v, "Re": Re, "Pr": Pr,
                    "h_W_m2K": h},
        "dT_K": {"film": dT_film, "clad": dT_clad, "gap": dT_gap, "fuel": dT_fuel},
        "T_hot_channel_out_C": T_hot_out - K0, "T_clad_peak_C": T_clad_out - K0, "T_fuel_peak_C": T_fuel_max - K0,
        "dP_core_kPa": dP_core / 1e3, "pumping_MW": pump / 1e6, "pumping_frac": pump / (P_MW * 1e6),
        "assumptions": f"q' avg {q_lin_avg/1e3:.0f} kW/m, k_fuel {k_fuel}, k_clad {k_clad}, h_gap {h_gap} W/m2K, "
                       f"F_q {F_Q}, F_dH {F_DH}, loop dP = {loop_factor} x core, pump eff {pump_eff} (all approx.)",
    }


def annulus_dT(q3, R_out, r_in, k):
    """Peak conduction rise in an annular cell heated uniformly, cooled at r_in, adiabatic at R_out."""
    return q3 / (4 * k) * (R_out ** 2 * (2 * math.log(R_out / r_in) - 1) + r_in ** 2)


out = {}
# B1: Li-7, (U,Pu)N, Nb-1Zr. Boiling margin rule (taxonomy rule 1): Tb(p) >= peak coolant + 300 K.
tb1 = thermo.boiling_point_K(con, "Li")[0]
out["Li_boiling"] = {"Tb_1bar_C": tb1 - K0, "Tb_5bar_C": tb_at_pressure("Li", 5) - K0,
                     "Tb_10bar_C": tb_at_pressure("Li", 10) - K0,
                     "max_peak_coolant_1bar_C": tb1 - 300 - K0,
                     "max_peak_coolant_10bar_C": tb_at_pressure("Li", 10) - 300 - K0,
                     "basis": "JANAF (db) vapour pressure; Clausius-Clapeyron above Tb (calc)"}
T_pk_B1 = 950 + F_DH * 150 + K0
lo, hi = 0.01, 50.0
for _ in range(60):
    mid = (lo * hi) ** 0.5
    lo, hi = (mid, hi) if tb_at_pressure("Li", mid) < T_pk_B1 + 300 else (lo, mid)
out["Li_boiling"]["B1_hot_channel_peak_C"] = T_pk_B1 - K0
out["Li_boiling"]["B1_pressure_for_300K_margin_bar"] = hi
out["Pb_boiling"] = {"Tb_1bar_C": thermo.boiling_point_K(con, "Pb")[0] - K0,
                     "max_peak_coolant_1bar_C": thermo.boiling_point_K(con, "Pb")[0] - 300 - K0}
out["B1"] = pin_core("B1", 1000, "Li", 950, 1100, 30e3, 3.0e-3, 0.1e-3, 0.6e-3, 20.0, 60.0, 10000.0, 1.20,
                     pump_eff=0.5, P_MPa=0.5)
out["B2"] = pin_core("B2", 1000, "Pb", 700, 900, 30e3, 3.0e-3, 0.1e-3, 0.8e-3, 20.0, 10.0, 10000.0, 1.25)
out["B3"] = pin_core("B3", 1000, "He", 600, 1000, 15e3, 3.0e-3, 0.1e-3, 0.7e-3, 20.0, 10.0, 10000.0, 1.42,
                     pump_eff=0.85, P_MPa=7.0)
# B3 natural-circulation decay heat after depressurisation: chimney H = 10 m, loss coefficient K = 15 (approx.)
b3 = out["B3"]
A_flow = b3["geometry"]["n_pins"] * (math.sqrt(3) / 2 * (1.42 * 7.6e-3) ** 2 - math.pi * 3.8e-3 ** 2)
nc = {}
for P in (7.0, 1.0, 0.1):
    pr = props("He", 1073.0, P)
    dT = 400.0
    dp_drive = pr["rho"] * 9.81 * 10.0 * dT / 1073.0
    v = math.sqrt(2 * dp_drive / (15.0 * pr["rho"]))
    Q = pr["rho"] * v * A_flow * pr["cp"] * dT
    nc[f"{P} MPa"] = {"Q_MW": Q / 1e6, "frac_of_nominal": Q / 1e9}
out["B3"]["pressure_for_1h_decay_heat_MPa"] = 7.0 * 0.013 / nc["7.0 MPa"]["frac_of_nominal"]
out["B3"]["natural_circulation"] = {"assumptions": "chimney 10 m, loop K = 15, core dT 400 K, He at 800 C (approx.)",
                                    "cases": nc, "decay_heat_frac_1h_approx": 0.013}

# B4: circulating chloride salt. Core and external loop volumes (approx.), precursor drift.
salt = props("salt", 1073.0)
P4, Tin4, Tout4 = 1000.0, 700.0, 900.0
mdot4 = P4 * 1e6 / (salt["cp"] * (Tout4 - Tin4))
Vdot4 = mdot4 / salt["rho"]
V_core, V_loop = 10.0, 10.0  # m3 (approx.: ~100 MW/m3 in core, external volume equal to core)
tc, tl = V_core / Vdot4, V_loop / Vdot4
# Pu-239 fast-fission six-group delayed-neutron data (Keepin, approx.)
lam = np.array([0.0129, 0.0311, 0.134, 0.331, 1.26, 3.21])
a = np.array([0.038, 0.280, 0.216, 0.328, 0.103, 0.035])
f_in = 1 - (1 - np.exp(-lam * tc)) * (1 - np.exp(-lam * tl)) / (lam * tc * (1 - np.exp(-lam * (tc + tl))))
beta_frac = float((a * f_in).sum())
fast_loop = {}
for V_l in (5.0, 10.0, 20.0):
    tl2 = V_l / Vdot4
    f2 = 1 - (1 - np.exp(-lam * tc)) * (1 - np.exp(-lam * tl2)) / (lam * tc * (1 - np.exp(-lam * (tc + tl2))))
    fast_loop[f"V_loop {V_l} m3"] = float((a * f2).sum())
out["B4"] = {"design": "B4", "P_MWth": P4, "T_in_C": Tin4, "T_out_C": Tout4, "salt_props": salt,
             "mdot_kg_s": mdot4, "Vdot_m3_s": Vdot4, "V_core_m3": V_core, "V_loop_m3": V_loop,
             "core_power_density_MW_m3": P4 / V_core,
             "residence_core_s": tc, "residence_loop_s": tl,
             "delayed_fraction_emitted_in_core": beta_frac, "delayed_fraction_vs_loop_volume": fast_loop,
             "beta_Pu239_approx": 0.0021, "beta_eff_circulating_approx": 0.0021 * beta_frac,
             "NaCl_vp_bar_at_1173K": thermo.vapor_pressure_bar(con, "ClNa", 1173.0)[0],
             "NaCl_melting_C": thermo.melting_point_K(con, "ClNa")[0] - K0,
             "assumptions": "salt cp 600 J/kgK, rho 3,300 kg/m3 (approx.); eutectic NaCl-UCl3 melts near 520 C (approx.); "
                            "6-group Pu-239 delayed data (Keepin, approx.)"}

# B5: Pb-cooled cermet block, coolant channels in a cermet matrix (inverted block S3)
P5, Tin5, Tout5 = 1000.0, 900.0, 1100.0
q_core5 = 150.0e6  # W/m3 core average (approx.)
V5 = P5 * 1e6 / q_core5
cermet_frac, pb_frac = 0.60, 0.35
q3_cermet_pk = F_Q * q_core5 / cermet_frac
r_c = 4.0e-3
R_cell = r_c / math.sqrt(pb_frac)        # cell (cermet + channel) equivalent radius (void lumped in cermet)
k_cermet = {"UN-W": 45.0, "UN-Mo": 40.0}  # approx.
pr5 = props("Pb", 0.5 * (Tin5 + Tout5) + K0)
mdot5 = P5 * 1e6 / (pr5["cp"] * (Tout5 - Tin5))
n_ch = V5 / 1.0 / (math.pi * R_cell ** 2)  # H = 1 m
v5 = mdot5 / pr5["rho"] / (n_ch * math.pi * r_c ** 2)
Re5 = pr5["rho"] * v5 * 2 * r_c / pr5["mu"]
Pr5 = pr5["mu"] * pr5["cp"] / pr5["k"]
h5 = nusselt("Pb", Re5, Pr5) * pr5["k"] / (2 * r_c)
q_wall_pk = q3_cermet_pk * math.pi * (R_cell ** 2 - r_c ** 2) / (2 * math.pi * r_c)
dP5 = darcy_f(Re5) * 1.0 / (2 * r_c) * pr5["rho"] * v5 ** 2 / 2
out["B5"] = {"design": "B5", "P_MWth": P5, "T_in_C": Tin5, "T_out_C": Tout5,
             "core_power_density_MW_m3": q_core5 / 1e6, "core_volume_m3": V5,
             "core_diameter_m_H1m": math.sqrt(4 * V5 / math.pi),
             "channel_radius_mm": r_c * 1e3, "cell_radius_mm": R_cell * 1e3, "n_channels": round(n_ch),
             "Pb_velocity_m_s": v5, "Re": Re5, "h_W_m2K": h5, "heat_flux_peak_MW_m2": q_wall_pk / 1e6,
             "T_hot_channel_out_C": Tin5 + F_DH * (Tout5 - Tin5),
             "dT_film_K": q_wall_pk / h5,
             "cases": {}, "dP_core_kPa": dP5 / 1e3,
             "pumping_MW": 2 * dP5 * mdot5 / pr5["rho"] / 0.75 / 1e6,
             "assumptions": "150 MW/m3 core average, cermet 60% / Pb 35% / void 5%, channel r 4 mm, H 1 m, "
                            "k cermet UN-W 45, UN-Mo 40 W/mK (approx.)"}
for kname, k in k_cermet.items():
    dTc = annulus_dT(q3_cermet_pk, R_cell, r_c, k)
    Tw = out["B5"]["T_hot_channel_out_C"] + q_wall_pk / h5
    out["B5"]["cases"][kname] = {"dT_conduction_K": dTc, "T_wall_peak_C": Tw, "T_cermet_peak_C": Tw + dTc}

# B6: heat-pipe monolith; Li heat-pipe sonic limit from JANAF vapour pressure and enthalpy of vaporisation
hp = {}
for T in (1300.0, 1400.0, 1500.0):
    p_bar = thermo.vapor_pressure_bar(con, "Li", T)[0]
    dH = h_vap_kJ("Li", T)  # kJ/mol monomer
    rho_v = p_bar * 1e5 * 6.94e-3 / (R * T)
    h_fg = dH / 6.94e-3 * 1e3  # J/kg
    A_v = math.pi * 0.008 ** 2  # 16 mm vapour core (approx.)
    Qs = 0.474 * A_v * h_fg * math.sqrt(rho_v * p_bar * 1e5)  # Busse/Levy sonic limit
    hp[T] = {"p_v_bar": p_bar, "h_fg_MJ_kg": h_fg / 1e6, "rho_v_kg_m3": rho_v, "sonic_limit_kW": Qs / 1e3}
P6, n_hp_kW, H6 = 10.0, 10.0, 1.5     # MWth, kW per pipe (capillary-limited, approx.), active height
n_hp = P6 * 1e3 / n_hp_kW
r_hp = 0.010
A_cell6 = math.pi * r_hp ** 2 / 0.20   # heat pipe takes 20% of the cell (walls + Li + vapour)
R6 = math.sqrt(A_cell6 / math.pi)
q3_6 = F_Q * n_hp_kW * 1e3 / H6 / A_cell6
dT6 = annulus_dT(q3_6, R6, r_hp, 30.0)
out["B6"] = {"design": "B6", "P_MWth": P6, "heat_pipe_kW": n_hp_kW, "n_heat_pipes": n_hp,
             "Li_heat_pipe_limits": hp, "core_diameter_m": math.sqrt(4 * n_hp * A_cell6 / math.pi), "H_m": H6,
             "core_power_density_MW_m3": P6 / (n_hp * A_cell6 * H6), "dT_monolith_K": dT6,
             "T_vapour_C": 1150.0, "T_fuel_peak_C": 1150.0 + 30.0 + dT6,
             "heat_pipes_for_1000MWth": 1000e3 / n_hp_kW,
             "core_diameter_for_1000MWth_m": math.sqrt(4 * 1000e3 / n_hp_kW * A_cell6 / math.pi),
             "assumptions": "10 kW per Li heat pipe (capillary-limited, approx.), OD 20 mm, vapour core 16 mm, "
                            "monolith k 30 W/mK (approx.), wall + wick dT 30 K (approx.), H 1.5 m"}

# ---- power cycle: Carnot, Curzon-Ahlborn and a recuperated, intercooled closed He Brayton ----
def brayton(T_hot_C, T_cold_C=35.0, eta_t=0.92, eta_c=0.89, eps=0.95, dp=0.05, n_ic=1, net_factor=0.95):
    g = 5.0 / 3.0
    cp = 2.5 * R / 4.0026e-3
    T3, T1 = T_hot_C + K0, T_cold_C + K0
    best = None
    for pr in np.linspace(1.5, 4.5, 121):
        pr_stage = pr ** (1.0 / (n_ic + 1))
        wc = (n_ic + 1) * cp * T1 * (pr_stage ** ((g - 1) / g) - 1) / eta_c
        T2 = T1 + wc / (n_ic + 1) / cp
        pr_t = pr * (1 - dp)
        T4 = T3 - eta_t * T3 * (1 - pr_t ** (-(g - 1) / g))
        wt = cp * (T3 - T4)
        T2r = T2 + eps * (T4 - T2)
        q_in = cp * (T3 - T2r)
        eta = (wt - wc) / q_in
        if best is None or eta > best[1]:
            best = (pr, eta)
    return {"pressure_ratio": best[0], "eta_gross": best[1], "eta_net": best[1] * net_factor}


cycle = {}
for d, T_out, dT_ihx in (("B1", 1100, 50), ("B2", 900, 50), ("B3", 1000, 0), ("B4", 900, 75), ("B5", 1100, 50),
                         ("B6", 1100, 50)):
    Th = T_out + K0
    cycle[d] = {"T_out_C": T_out, "carnot": 1 - T_SINK / Th, "curzon_ahlborn": 1 - math.sqrt(T_SINK / Th),
                "turbine_inlet_C": T_out - dT_ihx, "brayton_He": brayton(T_out - dT_ihx),
                "assumptions": "He closed Brayton, 1 intercooler, turbine 0.92, compressor 0.89, recuperator 0.95, "
                               f"5% pressure loss, compressor inlet 35 C, IHX approach {dT_ihx} K, net = 0.95 gross (approx.)"}
(HERE / "results" / "thermal.json").write_text(json.dumps(out, indent=1, default=float))
(HERE / "results" / "cycle.json").write_text(json.dumps(cycle, indent=1))
for k in ("B1", "B2", "B3"):
    o = out[k]
    print(k, f"Tclad {o['T_clad_peak_C']:.0f} Tfuel {o['T_fuel_peak_C']:.0f} q''pk {o['heat_flux_peak_MW_m2']:.2f} "
          f"v {o['coolant']['velocity_m_s']:.2f} dP {o['dP_core_kPa']:.0f} kPa pump {o['pumping_frac']*100:.2f}% "
          f"D {o['geometry']['core_diameter_m']:.2f} q3 {o['core_power_density_MW_m3']:.0f} dT {o['dT_K']}  vf {o['geometry']}")
print("Li", out["Li_boiling"])
print("B3 NC", out["B3"]["natural_circulation"])
print("B4", {k: out["B4"][k] for k in ("residence_core_s", "residence_loop_s", "delayed_fraction_emitted_in_core", "delayed_fraction_vs_loop_volume", "NaCl_vp_bar_at_1173K")})
print("B5", {k: out["B5"][k] for k in ("Pb_velocity_m_s", "heat_flux_peak_MW_m2", "dT_film_K", "cases", "dP_core_kPa", "pumping_MW", "core_diameter_m_H1m")})
print("B6", json.dumps(out["B6"], default=float)[:900])
for d, c in cycle.items():
    print(d, f"Carnot {c['carnot']:.3f} CA {c['curzon_ahlborn']:.3f} Brayton net {c['brayton_He']['eta_net']:.3f} PR {c['brayton_He']['pressure_ratio']:.2f}")

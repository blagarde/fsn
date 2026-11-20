"""Family A Phase 1 thermal sizing (1D) and power-cycle limits. Writes results/thermal.json.

A1: (U,Pu)N pin, ZrB2 (or W/AlN) cladding, liquid Al in a triangular lattice (geometry.py).
    Hot pin, chopped-cosine axial power, coolant/clad/gap/fuel resistances in series. For each average
    linear power, find the highest coolant outlet temperature with peak fuel centre <= T_FUEL_MAX.
A2: 1D sizing already on the A2 page (outlet ~1,750 C, peak fuel 2,100 C); only the cycle is computed.
A3: Al-U-Pu solution fuel-coolant: temperature window (liquidus to outlet), flow and the loss of
    delayed neutrons when precursors leave the core (6-group Pu-239 data, approx.).
Cycle: Carnot and Curzon-Ahlborn limits at the outlet with a 30 C sink; recuperated closed He Brayton
and a Brayton + steam combined cycle as realistic estimates.

All inputs below are (approx.) unless tagged (db).
"""
from __future__ import annotations

import json
import math
import sqlite3
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from geometry import A1_FRACTIONS  # noqa: E402

ROOT = HERE.parents[1]
T_SINK = 303.15

# --------------------------------------------------------------------------- properties
def al_cp_db() -> float:
    """Liquid Al Cp in J/(kg K) from NIST-JANAF (db); constant 31.751 J/(mol K) above the melting point."""
    from htfbr_data import thermo
    con = sqlite3.connect(ROOT / "data" / "htfbr.sqlite")
    con.row_factory = sqlite3.Row
    return thermo.interp(con, thermo.find_species(con, "Al", "cr,l"), "cp", 1600.0) / 26.982e-3


AL = {"rho": 2200.0, "mu": 0.7e-3, "k": 100.0}  # ~1,300 C (approx.); A2 page uses 2,100 / 0.6e-3 hotter
K_FUEL = 15.0       # (U,Pu)N, W/m K (approx.; UN ~20, Pu and porosity lower it)
H_GAP = 6000.0      # He-filled pellet-clad gap conductance, W/m2 K (approx.)
K_ZRB2 = 40.0       # irradiated guess, as A2 page
K_W, K_ALN = 100.0, 30.0
T_FUEL_MAX = 2273.15   # 2,000 C peak fuel centre: nitride dissociation/volatility guide (approx.)
ZRB2_MECH = {"E": 350e9, "alpha": 7.5e-6, "nu": 0.12, "allow": 100e6}   # as A2 page
H_ACTIVE = 1.2      # m, active height (approx.)
F_AXIAL = 1.25      # peak/average axial (chopped cosine)
F_RADIAL = 1.20     # hot-pin power factor (same flow per pin)
DT_CORE = 400.0     # K, core coolant temperature rise (design choice)
P_TH = 1000e6


def nusselt(Pe):
    return 4.82 + 0.0185 * Pe ** 0.827   # liquid metal, as A2 page


def a1_pin(q_avg: float, T_out: float, clad: str = "ZrB2") -> dict:
    g = A1_FRACTIONS["pin"]
    rf, rg, rc, p = (g[k] * 1e-3 for k in ("r_fuel_mm", "r_gap_mm", "r_clad_mm", "pitch_mm"))
    cell = math.sqrt(3) / 2 * p ** 2
    a_flow = cell - math.pi * rc ** 2
    dh = 4 * a_flow / (2 * math.pi * rc)
    cp = al_cp_db()
    T_in = T_out - DT_CORE
    mdot = q_avg * H_ACTIVE / (cp * DT_CORE)          # per average pin
    u = mdot / (AL["rho"] * a_flow)
    Pe = AL["rho"] * u * dh * cp / AL["k"]
    h = nusselt(Pe) * AL["k"] / dh
    # chopped cosine with extrapolated half-length L such that peak/avg = F_AXIAL
    z = np.linspace(-H_ACTIVE / 2, H_ACTIVE / 2, 401)
    Le = _extrap_length(F_AXIAL)
    shape = np.cos(np.pi * z / Le)
    shape /= shape.mean()
    q_lin = F_RADIAL * q_avg * shape
    Tc = T_in + np.concatenate([[0], np.cumsum((q_lin[1:] + q_lin[:-1]) / 2 * np.diff(z))]) / (mdot * cp)
    qpp = q_lin / (2 * math.pi * rc)
    T_wall = Tc + qpp / h
    if clad == "ZrB2":
        R_clad = math.log(rc / rg) / (2 * math.pi * K_ZRB2)
    else:  # 0.6 mm W inside, 0.2 mm AlN outside
        rm = rg + 0.6e-3
        R_clad = math.log(rm / rg) / (2 * math.pi * K_W) + math.log(rc / rm) / (2 * math.pi * K_ALN)
    T_ci = T_wall + q_lin * R_clad
    T_fs = T_ci + q_lin / (2 * math.pi * rf * H_GAP)
    T_fc = T_fs + q_lin / (4 * math.pi * K_FUEL)
    i = int(np.argmax(T_fc))
    dT_clad_peak = float((q_lin * R_clad).max())
    sigma_th = ZRB2_MECH["E"] * ZRB2_MECH["alpha"] * dT_clad_peak / (2 * (1 - ZRB2_MECH["nu"]))
    dp_core = _dp(u, dh, H_ACTIVE + 1.5)   # active + ~1.5 m plenum/shield length, friction only
    return {"q_avg_kW_m": q_avg / 1e3, "T_in_C": T_in - 273.15, "T_out_C": T_out - 273.15,
            "u_m_s": u, "h_kW_m2K": h / 1e3, "q_flux_peak_MW_m2": float(qpp.max() / 1e6),
            "T_fuel_peak_C": float(T_fc.max() - 273.15), "z_fuel_peak_m": float(z[i]),
            "T_clad_inner_peak_C": float(T_ci.max() - 273.15), "T_wall_peak_C": float(T_wall.max() - 273.15),
            "dT_film_gap_clad_fuel_at_peak_K": [float(qpp[i] / h), float(q_lin[i] / (2 * math.pi * rf * H_GAP)),
                                                 float(q_lin[i] * R_clad), float(q_lin[i] / (4 * math.pi * K_FUEL))],
            "sigma_thermal_ZrB2_MPa": sigma_th / 1e6 if clad == "ZrB2" else None,
            "dp_core_kPa": dp_core / 1e3}


def _extrap_length(F):
    from scipy.optimize import brentq
    f = lambda L: (np.pi * H_ACTIVE / (2 * L)) / math.sin(np.pi * H_ACTIVE / (2 * L)) - F
    return brentq(f, H_ACTIVE * 0.5001, H_ACTIVE * 50)


def _dp(u, dh, L):
    Re = AL["rho"] * u * dh / AL["mu"]
    f = 0.316 * Re ** -0.25 if Re > 3000 else 64 / Re
    return f * L / dh * AL["rho"] * u ** 2 / 2


def a1_sizing(clad="ZrB2"):
    from scipy.optimize import brentq
    rows = []
    for q in (15e3, 20e3, 25e3, 30e3, 40e3):
        fn = lambda T: a1_pin(q, T, clad)["T_fuel_peak_C"] + 273.15 - T_FUEL_MAX
        try:
            T_out = brentq(fn, 1000.0, 2400.0)
        except ValueError:
            continue
        r = a1_pin(q, T_out, clad)
        n_pins = P_TH / (q * H_ACTIVE)
        g = A1_FRACTIONS["pin"]
        cell = math.sqrt(3) / 2 * (g["pitch_mm"] * 1e-3) ** 2
        r["n_pins"] = n_pins
        r["core_volume_m3"] = n_pins * cell * H_ACTIVE
        r["fuel_mass_t"] = n_pins * math.pi * (g["r_fuel_mm"] * 1e-3) ** 2 * H_ACTIVE * 13600 / 1e3
        mdot = P_TH / (al_cp_db() * DT_CORE)
        r["Al_flow_kg_s"] = mdot
        r["pumping_core_kW"] = mdot / AL["rho"] * r["dp_core_kPa"] * 1e3 / 1e3 / 0.5   # 50% pump efficiency
        r["fission_gas"] = fission_gas(q, T_out)
        rows.append(r)
    return rows


def fission_gas(q_avg, T_out, burnup_fima=0.10, fgr=0.5, plenum_ratio=1.0):
    """End-of-life plenum pressure and ZrB2 hoop stress (approx.). 0.25 Xe+Kr atoms per fission (approx.);
    plenum volume = plenum_ratio x fuel volume at the outlet temperature; open porosity ignored."""
    g = A1_FRACTIONS["pin"]
    rf, rg, rc = (g[k] * 1e-3 for k in ("r_fuel_mm", "r_gap_mm", "r_clad_mm"))
    v_fuel = math.pi * rf ** 2      # per m of fuel
    n_hm = v_fuel * 13600 * 0.94 / 0.2386   # mol HM per m (HM mass fraction ~0.94 in (U,Pu)N)
    n_gas = n_hm * burnup_fima * 0.25 * fgr
    p = n_gas * 8.314 * T_out / (plenum_ratio * v_fuel)
    sigma = p * rc / (rc - rg)
    return {"burnup_FIMA": burnup_fima, "release_fraction": fgr, "plenum_to_fuel_volume": plenum_ratio,
            "p_EOL_MPa": p / 1e6, "hoop_stress_MPa": sigma / 1e6}


# --------------------------------------------------------------------------- A3
BETA_PU239 = {   # Keepin 6-group, fast fission of Pu-239 (approx.): (relative abundance, lambda 1/s)
    "a": [0.038, 0.280, 0.216, 0.328, 0.103, 0.035],
    "lam": [0.0129, 0.0311, 0.134, 0.331, 1.26, 3.21],
}
BETA_TOTAL_PU239 = 0.0021   # (approx.), as on the U-Pu material page


def precursor_retention(tau_c, tau_l):
    """Fraction of delayed neutrons emitted in core for fuel circulating with core/loop transit times
    (slug flow, uniform in-core production; standard circulating-fuel estimate)."""
    frac = 0.0
    for a, lam in zip(BETA_PU239["a"], BETA_PU239["lam"]):
        x, y = lam * tau_c, lam * tau_l
        f = 1 - (1 - math.exp(-x)) * (1 - math.exp(-y)) / (x * (1 - math.exp(-x - y)))
        frac += a * f
    return frac


def a3_sizing():
    cp_al_mol = 31.751           # J/mol K (db, JANAF liquid Al)
    cp_u_mol = 48.0              # liquid U, J/mol K (approx.)
    sys.path.insert(0, str(HERE))
    import materials as M
    rows = []
    for x, liq_C in ((1 / 3, 1620.0), (0.20, 1400.0)):
        rho, rho_hm = M.solution_density(x)
        Mmol = (1 - x) * 26.98 + x * 238.6
        cp = ((1 - x) * cp_al_mol + x * cp_u_mol) / (Mmol * 1e-3)
        T_out = 2000.0
        T_in = liq_C + 50.0
        dT = T_out - T_in
        mdot = P_TH / (cp * dT)
        Q = mdot / (rho * 1e3)
        for V_core, V_loop in ((10.0, 5.0), (10.0, 10.0), (20.0, 5.0)):
            tc, tl = V_core / Q, V_loop / Q
            ret = precursor_retention(tc, tl)
            rows.append({"x_hm": x, "density_g_cc": rho, "HM_density_g_cc": rho_hm, "cp_J_kgK": cp,
                         "liquidus_C_approx": liq_C, "T_in_C": T_in, "T_out_C": T_out, "dT_K": dT,
                         "mdot_kg_s": mdot, "Q_m3_s": Q, "V_core_m3": V_core, "V_loop_m3": V_loop,
                         "tau_core_s": tc, "tau_loop_s": tl, "delayed_retained_fraction": ret,
                         "beta_eff_pcm_approx": 1e5 * BETA_TOTAL_PU239 * ret,
                         "HM_out_of_core_fraction": V_loop / (V_core + V_loop)})
    return rows


# --------------------------------------------------------------------------- cycles
def cycle_limits(T_out_C: float) -> dict:
    Th = T_out_C + 273.15
    return {"T_out_C": T_out_C, "carnot": 1 - T_SINK / Th, "curzon_ahlborn": 1 - math.sqrt(T_SINK / Th),
            "brayton_recuperated": brayton(T_out_C, recup=True), "combined_cycle": combined(T_out_C),
            "brayton_recuperated_TIT1000": brayton(T_out_C, recup=True, tit_cap_C=1000.0),
            "combined_cycle_TIT1000": combined(T_out_C, tit_cap_C=1000.0)}


PLANT_FACTOR = 0.95   # generator, auxiliaries and IHX losses on top of the cycle (approx.)


def brayton(T_out_C, recup=True, tit_cap_C=1500.0, approach=50.0, eta_t=0.92, eta_c=0.88, eps=0.90, loss=0.08):
    """Closed He Brayton (gamma 5/3), TIT = min(outlet - approach, cap). Returns best net efficiency over
    pressure ratio, times PLANT_FACTOR. A 1,500 C cap needs ceramic or cooled blades; 1,000 C is closer to
    uncooled metallic He turbines (approx.)."""
    g = 5 / 3
    k = (g - 1) / g
    T1 = T_SINK + 5.0
    T3 = min(T_out_C - approach, tit_cap_C) + 273.15
    best = (0.0, None)
    for pr in np.linspace(1.3, 8.0, 300):
        T2 = T1 * (1 + (pr ** k - 1) / eta_c)
        T4 = T3 * (1 - eta_t * (1 - (pr * (1 - loss)) ** -k))
        wnet = (T3 - T4) - (T2 - T1)
        Tin_heater = T2 + eps * (T4 - T2) if recup and T4 > T2 else T2
        qin = T3 - Tin_heater
        if wnet > 0 and qin > 0 and wnet / qin > best[0]:
            best = (wnet / qin, float(pr))
    return {"eta": best[0] * PLANT_FACTOR, "pressure_ratio": best[1], "TIT_C": T3 - 273.15}


def combined(T_out_C, eta_steam=0.38, stack_C=120.0, tit_cap_C=1500.0):
    """Unrecuperated He Brayton topping; turbine exhaust heat above stack_C feeds a steam cycle
    (eta_steam on that heat, approx.). Times PLANT_FACTOR."""
    g = 5 / 3
    k = (g - 1) / g
    T1 = T_SINK + 5.0
    T3 = min(T_out_C - 50.0, tit_cap_C) + 273.15
    best = (0.0, None)
    for pr in np.linspace(1.5, 12.0, 400):
        T2 = T1 * (1 + (pr ** k - 1) / 0.88)
        T4 = T3 * (1 - 0.92 * (1 - (pr * 0.94) ** -k))
        qin = T3 - T2
        wb = (T3 - T4) - (T2 - T1)
        q_rec = max(T4 - max(T2, stack_C + 273.15), 0.0)
        if qin <= 0 or wb <= 0:
            continue
        eta = (wb + eta_steam * q_rec) / qin
        if eta > best[0]:
            best = (eta, float(pr))
    return {"eta": best[0] * PLANT_FACTOR, "pressure_ratio": best[1], "TIT_C": T3 - 273.15}


def main():
    out = {
        "inputs": {"Al_cp_J_kgK_db": al_cp_db(), "Al": AL, "K_FUEL": K_FUEL, "H_GAP": H_GAP, "K_ZRB2": K_ZRB2,
                   "T_FUEL_MAX_C": T_FUEL_MAX - 273.15, "H_ACTIVE": H_ACTIVE, "F_AXIAL": F_AXIAL,
                   "F_RADIAL": F_RADIAL, "DT_CORE": DT_CORE, "P_TH_MW": P_TH / 1e6},
        "A1_ZrB2": a1_sizing("ZrB2"),
        "A1_WAlN": a1_sizing("W/AlN"),
        "A3": a3_sizing(),
        "cycles": {k: cycle_limits(t) for k, t in
                   (("A1_1300C", 1300.0), ("A1_1500C", 1500.0), ("A2_1750C", 1750.0), ("A2_1700C_PbBond", 1700.0),
                    ("A3_2000C", 2000.0), ("ref_550C", 550.0))},
    }
    (HERE / "results" / "thermal.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

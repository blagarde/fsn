"""Thermal and geometric scoping of the new core-geometry candidates (S5, S6, S8, S9, L3, L5, L7).

Every property here is approximate (handbook-class, labelled PROPS); the point is the governing
limit and the size it implies for 1,000 MWth, not a design. Writes results/thermal.json.
Run: python thermal.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

SIGMA = 5.670374e-8
P_TH = 1.0e9          # W, 1,000 MWth
G = 9.81
K0 = 273.15
OUT = Path(__file__).parent / "results"

# ---------------------------------------------------------------- approximate properties
PROPS = {
    "k_UPu_liquid": 40.0,       # W/m K (A2 assumption, 30-50)
    "rho_UPu_liquid": 16000.0,  # kg/m3
    "mu_UPu_liquid": 3.0e-3,    # Pa s near 2,000 C (approx.; ~6 mPa s near the melting point)
    "k_UN": 20.0,               # W/m K at 1,500-2,000 C (approx.)
    "rho_UN": 13600.0,
    "k_W": 100.0, "k_Mo": 100.0, "k_AlN": 30.0,
    "h_Al": 90e3,               # W/m2 K (A2 sizing, Nu = 4.82 + 0.0185 Pe^0.827)
    "eps_W_bare": 0.30,         # total hemispherical, ~2,000 C (approx.)
    "eps_coated": 0.80,         # textured W or carbide coating (approx., to be measured)
    "eps_AlN": 0.80,            # receiver side (approx.)
    "cp_He": 5193.0,
    "cp_Pb": 140.0, "cp_Al": 1177.0,   # Al: JANAF 1.177 kJ/kg K at 1,000 C (db)
    "cp_Al2O3": 1258.0,         # JANAF at 1,200 K (db, results/db_facts.json)
    "rho_Al2O3": 3950.0,
}


def he_props(T, p_bar=70.0):
    """KTA-type helium correlations (approx.)."""
    rho = p_bar * 1e5 / (2077.0 * T)
    mu = 3.674e-7 * T ** 0.7
    k = 2.682e-3 * (1 + 1.123e-3 * p_bar) * T ** (0.71 * (1 - 2e-4 * p_bar))
    return rho, mu, k


def pb_props(T):
    """Lead (OECD/NEA handbook-type correlations, approx.)."""
    return 11441 - 1.2795 * T, 4.55e-4 * math.exp(1069 / T), 9.2 + 0.011 * T


def gas_k(gas, T):
    """Low-pressure gas conductivity, power law in T (approx.)."""
    k300, n = {"He": (0.155, 0.71), "N2": (0.026, 0.80), "Ar": (0.0177, 0.73)}[gas]
    return k300 * (T / 300) ** n


# ---------------------------------------------------------------- radiation
def q_rad(Th_C, Tc_C, e1, e2):
    Th, Tc = Th_C + K0, Tc_C + K0
    return SIGMA * (Th ** 4 - Tc ** 4) / (1 / e1 + 1 / e2 - 1)


def q_rad_local(Th_C, Tcool_C, e1, e2, R_cold):
    """Flux to a cooled panel whose surface sits q*R_cold above the coolant (fixed point)."""
    q = q_rad(Th_C, Tcool_C, e1, e2)
    for _ in range(50):
        q = 0.5 * q + 0.5 * q_rad(Th_C, Tcool_C + q * R_cold, e1, e2)
    return q


def q_avg_isothermal_hot(Th_C, Tin_C, Tout_C, e1, e2, R_cold, n=400):
    """Hot surface uniform (convecting liquid fuel); coolant heats from Tin to Tout.
    Area = m cp * integral dT / q(T), so q_avg is the harmonic mean over coolant temperature."""
    dT = (Tout_C - Tin_C) / n
    integral = sum(dT / q_rad_local(Th_C, Tin_C + (i + 0.5) * dT, e1, e2, R_cold) for i in range(n))
    return (Tout_C - Tin_C) / integral


def q_uniform_flux(Th_C, Tout_C, e1, e2, R_cold):
    """Bounding case for unzoned solid fuel: uniform power, hottest surface where coolant is hottest."""
    return q_rad_local(Th_C, Tout_C, e1, e2, R_cold)


# ---------------------------------------------------------------- radiative plate cell
def plate_cell(t_fuel, t_can, gap, t_panel_wall, t_channel):
    """Repeating cell: fuel slab | can | gap | panel (wall, channel, wall) | gap | can | ...
    Two faces of every slab radiate; returns volume fractions and radiating area per core volume."""
    pitch = t_fuel + 2 * t_can + 2 * gap + 2 * t_panel_wall + t_channel
    return {
        "pitch_mm": pitch * 1e3,
        "fractions": {"fuel": t_fuel / pitch, "can": 2 * t_can / pitch, "gap": 2 * gap / pitch,
                      "panel_wall": 2 * t_panel_wall / pitch, "coolant": t_channel / pitch},
        "area_per_volume_m2_m3": 2 / pitch,
    }


def tube_row_cell(r_i, t_can, tube_gap, gap, t_panel_wall, t_channel, e1, e2):
    """Row of fuel tubes (inner radius r_i) between two cooled panels. Tube-to-tube exchange carries no net
    heat, so each tube and the panel strip it faces form a two-surface enclosure:
    q_tube = sigma (Th^4 - Tc^4) / (1/e1 + (A1/A2)(1/e2 - 1)). Returns fractions and the factor that
    converts the plate flux into a flux per core volume."""
    r_o = r_i + t_can
    s = 2 * r_o + tube_gap
    pitch = 2 * r_o + 2 * gap + 2 * t_panel_wall + t_channel
    A1, A2 = 2 * math.pi * r_o, 2 * s
    cellA = s * pitch
    plate_res = 1 / e1 + 1 / e2 - 1
    tube_res = 1 / e1 + (A1 / A2) * (1 / e2 - 1)
    return {
        "pitch_mm": pitch * 1e3, "tube_pitch_mm": s * 1e3,
        "fractions": {"fuel": math.pi * r_i ** 2 / cellA, "can": math.pi * (r_o ** 2 - r_i ** 2) / cellA,
                      "panel_wall": 2 * t_panel_wall * s / cellA, "coolant": t_channel * s / cellA,
                      "gap": 1 - (math.pi * r_o ** 2 + (2 * t_panel_wall + t_channel) * s) / cellA},
        # radiating (panel) area per core volume, with the tube enclosure correction folded in
        "area_per_volume_m2_m3": (A1 / cellA) * plate_res / tube_res,
        "tube_area_per_volume_m2_m3": A1 / cellA,
        "A1_over_A2": A1 / A2,
    }


def radiative_core(cell, q_avg, rho_fuel, a_half, k_fuel):
    V = P_TH / (q_avg * cell["area_per_volume_m2_m3"])
    fuel_mass = V * cell["fractions"]["fuel"] * rho_fuel
    return {
        "q_avg_MW_m2": q_avg / 1e6,
        "radiating_area_m2": P_TH / q_avg,
        "core_volume_m3": V,
        "core_power_density_MW_m3": P_TH / V / 1e6,
        "equivalent_cylinder_D_eq_H_m": (4 * V / math.pi) ** (1 / 3),
        "fuel_mass_t": fuel_mass / 1e3,
        "specific_power_MW_per_t": P_TH / fuel_mass / 1e3,
        "fuel_dT_centre_K": q_avg * a_half / (2 * k_fuel),
    }


def l7():
    res = {"assumptions": {
        "Tin_C": 1000, "container": "1.0 mm W can, emissivity 0.30 bare or 0.80 coated (approx.)",
        "gap_mm": 2.0, "panel": "1 mm AlN walls + 4 mm Al channel (reference); Pb in 1 mm Mo; He in 1 mm Mo",
        "fuel": "liquid U-Pu, k 40 W/m K, 16 t/m3, conduction only (convection would lower the drop)",
        "hot_surface": "uniform (liquid fuel convects vertically if the coolant inlet is at the top)"}}
    R = {"Al/AlN": 0.001 / PROPS["k_AlN"] + 1 / PROPS["h_Al"],
         "Pb/Mo": 0.001 / PROPS["k_Mo"] + 1 / 25e3,      # Pb h ~25 kW/m2K (approx.)
         "He/Mo": 0.001 / PROPS["k_Mo"] + 1 / 4e3}       # He 7 MPa h ~4 kW/m2K (approx.)
    res["R_cold_m2K_W"] = R
    # check against the study table (two plates, cold wall 1,300 C)
    res["check_study_table_MW_m2"] = {f"{Th}C": {"black": q_rad(Th, 1300, 1, 1) / 1e6,
                                                 "0.8/0.8": q_rad(Th, 1300, .8, .8) / 1e6,
                                                 "0.3/0.8": q_rad(Th, 1300, .3, .8) / 1e6}
                                      for Th in (1500, 1800, 2000, 2200)}
    grid = []
    for Th in (2000, 2200):
        for Tout in (1300, 1500, 1700):
            for eps_name, e1 in (("bare W 0.3", PROPS["eps_W_bare"]), ("coated 0.8", PROPS["eps_coated"])):
                for cool, Rc in R.items():
                    q = q_avg_isothermal_hot(Th, 1000, Tout, e1, PROPS["eps_AlN"], Rc)
                    qu = q_uniform_flux(Th, Tout, e1, PROPS["eps_AlN"], Rc)
                    grid.append({"Th_C": Th, "Tout_C": Tout, "emissivity": eps_name, "coolant": cool,
                                 "q_avg_isothermal_MW_m2": q / 1e6, "q_uniform_flux_MW_m2": qu / 1e6,
                                 "area_isothermal_m2": P_TH / q, "area_uniform_m2": P_TH / qu})
    res["flux_grid"] = grid
    # receiver emissivity sensitivity (coated W can 0.8, can 2,000 C, coolant 1,000 -> 1,500 C)
    res["receiver_emissivity"] = {f"eps2={e2}": q_avg_isothermal_hot(2000, 1000, 1500, 0.8, e2, R["Pb/Mo"]) / 1e6
                                  for e2 in (0.25, 0.5, 0.8, 0.9)}
    # coolant mass flows for 1,000 MWth, 1,000 -> 1,500 C
    res["mass_flow_kg_s"] = {"Al": P_TH / (PROPS["cp_Al"] * 500), "Pb": P_TH / (PROPS["cp_Pb"] * 500),
                             "He": P_TH / (PROPS["cp_He"] * 500)}
    # He in Mo tubes at 7 MPa: hoop stress for 4 mm bore, 1 mm wall
    res["He_tube_hoop_MPa_4mm_bore_1mm_wall"] = 7.0 * 2.0 / 1.0
    # reference and slab-thickness sweep (coated W, Al/AlN panel, Th 2,000, Tout 1,500)
    sweep = []
    for t_fuel_mm in (10, 20, 30, 40):
        cell = plate_cell(t_fuel_mm / 1e3, 1e-3, 2e-3, 1e-3, 4e-3)
        for Th, Tout, e1 in ((2000, 1500, 0.8), (2000, 1300, 0.8), (2200, 1500, 0.8), (2000, 1500, 0.3)):
            q = q_avg_isothermal_hot(Th, 1000, Tout, e1, PROPS["eps_AlN"], R["Al/AlN"])
            core = radiative_core(cell, q, PROPS["rho_UPu_liquid"], t_fuel_mm / 2e3, PROPS["k_UPu_liquid"])
            # peak flux (cold top end) sets the fuel peak
            qmax = q_rad_local(Th, 1000, e1, PROPS["eps_AlN"], R["Al/AlN"])
            core["q_peak_MW_m2"] = qmax / 1e6
            core["fuel_peak_C"] = Th + qmax * (1e-3 / PROPS["k_W"] + t_fuel_mm / 2e3 / (2 * PROPS["k_UPu_liquid"]))
            sweep.append({"t_fuel_mm": t_fuel_mm, "Th_C": Th, "Tout_C": Tout, "eps_container": e1,
                          "cell": cell, **core})
    res["slab_sweep"] = sweep
    tubes = []
    for r_i_mm in (7.5, 10.0, 15.0):
        for Th, Tout, e1 in ((2000, 1500, 0.8), (2200, 1500, 0.8), (2000, 1500, 0.3)):
            cell = tube_row_cell(r_i_mm / 1e3, 1e-3, 1e-3, 2e-3, 1e-3, 4e-3, e1, PROPS["eps_AlN"])
            q = q_avg_isothermal_hot(Th, 1000, Tout, e1, PROPS["eps_AlN"], R["Al/AlN"])  # plate-equivalent flux
            core = radiative_core(cell, q, PROPS["rho_UPu_liquid"], r_i_mm / 1e3, PROPS["k_UPu_liquid"])
            q_tube = q * cell["area_per_volume_m2_m3"] / cell["tube_area_per_volume_m2_m3"]
            qmax = q_rad_local(Th, 1000, e1, PROPS["eps_AlN"], R["Al/AlN"]) * q_tube / q
            core["q_tube_surface_avg_MW_m2"] = q_tube / 1e6
            core["fuel_dT_centre_K"] = q_tube * (r_i_mm + 1) / 1e3 / (2 * PROPS["k_UPu_liquid"])
            core["fuel_peak_C"] = Th + qmax * (1e-3 / PROPS["k_W"] + (r_i_mm + 1) / 1e3 / (2 * PROPS["k_UPu_liquid"]))
            tubes.append({"r_i_mm": r_i_mm, "Th_C": Th, "Tout_C": Tout, "eps_container": e1, "cell": cell, **core})
    res["tube_sweep"] = tubes
    # gap gas conduction, 2 mm, hot 2,000 / cold 1,400
    Th, Tc, gap = 2000 + K0, 1400 + K0, 2e-3
    Tm = 0.5 * (Th + Tc)
    res["gap_conduction_MW_m2"] = {g: gas_k(g, Tm) * (Th - Tc) / gap / 1e6 for g in ("He", "N2", "Ar")}
    res["gap_radiation_same_temps_MW_m2"] = {"bare W": q_rad(2000, 1400, .3, .8) / 1e6,
                                             "coated": q_rad(2000, 1400, .8, .8) / 1e6}
    # Rayleigh number in the gap (He, 1 bar): convection negligible if Ra << 1,000
    rho = 1e5 / (2077 * Tm); mu = 3.674e-7 * Tm ** 0.7; k = gas_k("He", Tm)
    alpha = k / (rho * 5193); nu = mu / rho
    res["gap_Ra_He_1bar_height_1m_based_on_gap"] = G * (1 / Tm) * (Th - Tc) * gap ** 3 / (nu * alpha)
    # AlN facing vacuum: free (Hertz-Knudsen) evaporation, evaporation coefficient 1 (upper bound)
    db = json.loads((OUT / "db_facts.json").read_text())["AlN_decomposition"]
    evap = {}
    for TC in ("1200", "1300", "1400", "1500"):
        pAl = db[TC]["vacuum_congruent_pAl_bar"] * 1e5
        pN2 = db[TC]["vacuum_congruent_pN2_bar"] * 1e5
        T = float(TC) + K0
        jAl = pAl * math.sqrt(0.02698 / (2 * math.pi * 8.314 * T))     # kg/m2 s of Al
        mol = jAl / 0.02698                                           # mol AlN / m2 s
        rate = mol * 0.04099 / 3260 * 3.156e7 * 1e3                    # mm/year of AlN
        # with 1 bar N2 in the gap: p_Al = K / sqrt(pN2)
        K = db[TC]["vacuum_congruent_pAl_bar"] * math.sqrt(db[TC]["vacuum_congruent_pN2_bar"])
        evap[TC] = {"pAl_vacuum_Pa": pAl, "recession_mm_per_year_alpha1": rate,
                    "pAl_under_1bar_N2_bar": K / 1.0, "suppression_factor_1bar_N2": db[TC]["vacuum_congruent_pAl_bar"] / K}
    res["AlN_in_vacuum"] = evap
    # Structural: hydrostatic head on the can (liquid fuel, outside is gap gas or vacuum)
    st = {}
    for H in (0.5, 1.0, 2.5):
        p = PROPS["rho_UPu_liquid"] * G * H
        st[f"{H} m column"] = {"p_MPa": p / 1e6,
                               "plate_span10mm_t1mm_bending_MPa": 0.5 * p * (10 / 1) ** 2 / 1e6,
                               "plate_span20mm_t1mm_bending_MPa": 0.5 * p * (20 / 1) ** 2 / 1e6,
                               "tube_r10mm_t1mm_hoop_MPa": p * 10 / 1 / 1e6}
    res["hydrostatic"] = st
    # Decay heat: radiating from the cans to an un-cooled (but intact) panel stack is not a sink;
    # vessel radiation as in A2: 20 m2 at 2,000 C, emissivity 0.3, to 300 C
    res["decay_heat_vessel_20m2_MW"] = 20 * q_rad(2000, 300, .3, .8) / 1e6
    return res


def s9():
    """Radiating solid fuel plates: (U,Pu)N 14 mm + 0.5 mm W can each side, 2 mm gaps, AlN/Al panel."""
    cell = plate_cell(14e-3, 0.5e-3, 2e-3, 1e-3, 4e-3)
    R = 0.001 / PROPS["k_AlN"] + 1 / PROPS["h_Al"]
    out = {"cell": cell}
    for e1 in (0.3, 0.8):
        for Th, Tout in ((2000, 1500), (2000, 1300), (1800, 1300)):
            qu = q_uniform_flux(Th, Tout, e1, PROPS["eps_AlN"], R)
            qz = q_avg_isothermal_hot(Th, 1000, Tout, e1, PROPS["eps_AlN"], R)  # power zoned to match
            for tag, q in (("unzoned", qu), ("zoned", qz)):
                c = radiative_core(cell, q, PROPS["rho_UN"], 7e-3, PROPS["k_UN"])
                out[f"eps{e1}_Th{Th}_Tout{Tout}_{tag}"] = c
    return out


def s5():
    """Fluidised bed: superficial velocity is pinned between minimum fluidisation and terminal velocity."""
    out = {}
    dp_rho = PROPS["rho_UN"]
    for d_mm in (1.0, 3.0):
        d = d_mm / 1e3
        # Helium, 7 MPa, mean 900 C
        rho, mu, k = he_props(1173.0)
        Ar = d ** 3 * rho * (dp_rho - rho) * G / mu ** 2
        Re_mf = math.sqrt(33.7 ** 2 + 0.0408 * Ar) - 33.7       # Wen-Yu
        u_mf = Re_mf * mu / (rho * d)
        for mult in (2, 4):
            u = mult * u_mf
            q_area = rho * u * PROPS["cp_He"] * 600                # He 600 -> 1,200 C
            out[f"He7MPa_d{d_mm}mm_{mult}umf"] = {"u_mf_m_s": u_mf, "u_m_s": u, "q_per_bed_area_MW_m2": q_area / 1e6,
                                                  "bed_area_for_1GW_m2": P_TH / q_area,
                                                  "bed_diameter_m": math.sqrt(4 * P_TH / q_area / math.pi)}
        # Lead fluidisation (homogeneous), 1,000 -> 1,400 C, mean 1,473 K
        rhol, mul, kl = pb_props(1473.0)
        Arl = d ** 3 * rhol * (dp_rho - rhol) * G / mul ** 2
        Re_t = (Arl / 13.9) ** (1 / 1.4) if Arl < 3e5 else 1.74 * math.sqrt(Arl)   # Allen / Newton (approx.)
        u_t = Re_t * mul / (rhol * d)
        n_rz = 2.39 if Re_t > 500 else 4.45 * Re_t ** -0.1
        for eps in (0.5, 0.6):
            u = u_t * eps ** n_rz
            q_area = rhol * u * PROPS["cp_Pb"] * 400
            out[f"Pb_d{d_mm}mm_voidage{eps}"] = {"u_t_m_s": u_t, "u_m_s": u, "q_per_bed_area_MW_m2": q_area / 1e6,
                                                 "bed_area_for_1GW_m2": P_TH / q_area}
    out["bed_dp_per_m_He_kPa"] = 0.5 * dp_rho * G / 1e3
    out["note"] = ("u_mf from Wen-Yu, u_t from Allen/Newton drag, Richardson-Zaki expansion; particle density "
                   "13.6 t/m3 (UN). The heat a bed can carry per unit cross-section is fixed by the fluidisation "
                   "window, so a 1 GWth bed is wide and flat unless the bed rotates (higher effective g).")
    # rotating bed: u_mf scales ~ g^0.5 in the inertial regime
    out["rotating_bed_gain_at_100g_approx"] = math.sqrt(100)
    return out


def s6():
    """Printed lattice, He 7 MPa: heat transfer is not limiting; pumping is."""
    rho, mu, k = he_props(1173.0)
    V, H = 10.0, 2.0                    # 100 MW/m3 core, 2 m tall
    A = V / H
    flow_frac, dh, a_surf = 0.40, 1.5e-3, 1000.0
    mdot = P_TH / (PROPS["cp_He"] * 600)
    Gm = mdot / (A * flow_frac)
    u = Gm / rho
    Re = Gm * dh / mu
    f = 0.316 * Re ** -0.25
    dp = f * H / dh * rho * u ** 2 / 2
    Pr = PROPS["cp_He"] * mu / k
    fg = (0.79 * math.log(Re) - 1.64) ** -2
    Nu = (fg / 8) * (Re - 1000) * Pr / (1 + 12.7 * math.sqrt(fg / 8) * (Pr ** (2 / 3) - 1))   # Gnielinski
    h = Nu * k / dh
    q_surf = P_TH / (V * a_surf)
    return {"core_volume_m3": V, "mdot_kg_s": mdot, "velocity_m_s": u, "Re": Re, "dp_kPa": dp / 1e3,
            "pumping_MW": mdot * dp / rho / 1e6, "h_W_m2K": h, "surface_flux_MW_m2": q_surf / 1e6,
            "film_dT_K": q_surf / h, "strut_dT_K_halfwidth0.5mm_k20": (P_TH / V / 0.55) * (0.5e-3) ** 2 / (2 * 20),
            "note": "gyroid surface density ~1,000 m2/m3 (approx.); solid fraction 0.55-0.60"}


def s8():
    """Particle-cooled pins: wall-to-moving-packed-bed heat transfer coefficient limits the flux."""
    r_o, pitch = 4.5e-3, 13e-3                 # pin OD 9 mm (8 mm fuel, 0.5 mm Mo clad), square pitch 13 mm
    a = 2 * math.pi * r_o / pitch ** 2
    out = {"surface_per_volume_m2_m3": a,
           "fractions": {"fuel": math.pi * 4e-3 ** 2 / pitch ** 2,
                         "clad": math.pi * (r_o ** 2 - 4e-3 ** 2) / pitch ** 2,
                         "channel": 1 - math.pi * r_o ** 2 / pitch ** 2}}
    for h in (300.0, 600.0, 1000.0):
        q = h * 300.0                           # clad surface 300 K above mean particle temperature
        V = P_TH / (q * a)
        out[f"h{int(h)}"] = {"q_MW_m2": q / 1e6, "core_volume_m3": V, "power_density_MW_m3": P_TH / V / 1e6}
    mdot = P_TH / (PROPS["cp_Al2O3"] * 500)     # particles 700 -> 1,200 C
    Vref = out["h600"]["core_volume_m3"]
    H = 2.5
    flow_area = Vref / H * out["fractions"]["channel"]
    out["particle_mdot_kg_s"] = mdot
    out["particle_velocity_m_s_at_h600_H2.5m"] = mdot / (0.58 * PROPS["rho_Al2O3"] * flow_area)
    out["note"] = ("h for dense granular flow along a wall ~200-1,000 W/m2 K at 700-1,200 C (approx.; falling-"
                   "particle receiver and moving-bed exchanger literature, to be sourced)")
    return out


def l3():
    """Liquid-fuel pins, 9 mm bore: Al coolant (0.8 mm W + 0.3 mm AlN duplex) or Pb coolant (0.8 mm W)."""
    r = 4.5e-3
    out = {}
    for q in (1e6, 2e6, 3e6):
        out[f"q{q/1e6:.0f}MW_m2_fuel_dT_K"] = q * r / (2 * PROPS["k_UPu_liquid"])
    rw = r + 0.8e-3
    od = 2 * (rw + 0.3e-3)
    pitch = 1.12 * od                         # triangular lattice, p/d 1.12
    cell = math.sqrt(3) / 2 * pitch ** 2
    out["geometry_Al"] = {"bore_mm": 9.0, "od_mm": od * 1e3, "pitch_mm": pitch * 1e3}
    out["fractions_Al"] = {"fuel": math.pi * r ** 2 / cell, "W": math.pi * (rw ** 2 - r ** 2) / cell,
                           "AlN": math.pi * ((od / 2) ** 2 - rw ** 2) / cell,
                           "coolant": 1 - math.pi * (od / 2) ** 2 / cell}
    od2 = 2 * rw
    p2 = 1.12 * od2
    cell2 = math.sqrt(3) / 2 * p2 ** 2
    out["geometry_Pb"] = {"bore_mm": 9.0, "od_mm": od2 * 1e3, "pitch_mm": p2 * 1e3}
    out["fractions_Pb"] = {"fuel": math.pi * r ** 2 / cell2, "W": math.pi * (rw ** 2 - r ** 2) / cell2,
                           "coolant": 1 - math.pi * rw ** 2 / cell2}
    a = math.pi * od / cell
    for q in (2e6, 3e6):
        V = P_TH / (q * a)
        out[f"core_volume_m3_q{q/1e6:.0f}"] = V
        out[f"fuel_mass_t_q{q/1e6:.0f}"] = V * out["fractions_Al"]["fuel"] * PROPS["rho_UPu_liquid"] / 1e3
    return out


def l5():
    """Falling film of liquid U-Pu on both faces of a cooled panel (turbulent film, Brauer correlation)."""
    mu, rho, k = PROPS["mu_UPu_liquid"], PROPS["rho_UPu_liquid"], PROPS["k_UPu_liquid"]
    nu = mu / rho
    out = {}
    for delta_mm in (1.0, 2.0, 3.0):
        d = delta_mm / 1e3
        scale = (3 * nu ** 2 / G) ** (1 / 3)
        Re = (d / (0.302 * scale)) ** (15 / 8)
        Gam = Re * mu / 4
        u = Gam / (rho * d)
        # cell: film | W 1.2 | AlN 0.3 | Al 4 | AlN 0.3 | W 1.2 | film | free gas space 3 mm
        pitch = 2 * d + 2 * 1.5e-3 + 4e-3 + 3e-3
        q = 3e6
        out[f"film_{delta_mm}mm"] = {
            "Re_film": Re, "velocity_m_s": u, "residence_in_2.5m_core_s": 2.5 / u,
            "fuel_dT_K_at_3MW_m2": q * d / (2 * k),
            "fractions": {"fuel": 2 * d / pitch, "W": 2 * 1.2e-3 / pitch, "AlN": 2 * 0.3e-3 / pitch,
                          "coolant": 4e-3 / pitch, "gas": 3e-3 / pitch},
            "core_volume_m3_at_3MW_m2": P_TH / (q * 2 / pitch),
            "fuel_in_core_t": P_TH / (q * 2 / pitch) * 2 * d / pitch * rho / 1e3}
    return out


def main():
    OUT.mkdir(exist_ok=True)
    res = {"properties_approx": PROPS, "L7": l7(), "S9": s9(), "S5": s5(), "S6": s6(), "S8": s8(),
           "L3": l3(), "L5": l5()}
    (OUT / "thermal.json").write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    r = main()
    L = r["L7"]
    print("study-table check", json.dumps(L["check_study_table_MW_m2"], indent=0))
    for s in L["slab_sweep"]:
        print(f"slab {s['t_fuel_mm']} Th {s['Th_C']} Tout {s['Tout_C']} e {s['eps_container']}: q {s['q_avg_MW_m2']:.3f} "
              f"V {s['core_volume_m3']:.1f} fuel {s['fuel_mass_t']:.0f} t ff {s['cell']['fractions']['fuel']:.3f} "
              f"peak {s['fuel_peak_C']:.0f} sp {s['specific_power_MW_per_t']:.1f}")
    for t in L["tube_sweep"]:
        print(f"tube r{t['r_i_mm']} Th {t['Th_C']} e {t['eps_container']}: qtube {t['q_tube_surface_avg_MW_m2']:.3f} V {t['core_volume_m3']:.1f} "
              f"fuel {t['fuel_mass_t']:.0f} t fr {json.dumps({k: round(v,4) for k,v in t['cell']['fractions'].items()})} peak {t['fuel_peak_C']:.0f} sp {t['specific_power_MW_per_t']:.1f}")
    for g in L["flux_grid"]:
        print(g["Th_C"], g["Tout_C"], g["emissivity"], g["coolant"], f"{g['q_avg_isothermal_MW_m2']:.3f} {g['q_uniform_flux_MW_m2']:.3f}")
    for k in ("gap_conduction_MW_m2", "gap_radiation_same_temps_MW_m2", "gap_Ra_He_1bar_height_1m_based_on_gap",
              "AlN_in_vacuum", "hydrostatic", "decay_heat_vessel_20m2_MW"):
        print(k, json.dumps(L[k], indent=0))
    for k in ("S9", "S5", "S6", "S8", "L3", "L5"):
        print(k, json.dumps(r[k], indent=0)[:3000])

"""Reference sizing of the proposed design: an array of sealed liquid U-Pu "pressure-cooker" pins with a
boiling Pb cap, immersed in flowing liquid Al (thermostat mode). Writes results/design.json.

Pin: W-25Re tube (structural) + TiB2 outer layer (Al side); liquid U-Pu column = active core; a thin Pb
layer floats on the fuel; above it a gas plenum (Ar + Pb vapour) joined to a common pressure header
whose pressure sets the Pb saturation temperature, i.e. the fuel temperature cap.
Run: /opt/mamba/envs/nuc/bin/python design.py
"""
import json
import math
import sys
from pathlib import Path

import model as M

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "core-thermal"))
import props  # noqa: E402

P_TH = 1.0e9
r_fuel = 0.025          # m, fuel radius (tube bore)
t_metal, t_barrier = 1.5e-3, 1.0e-3
q2_design = 3.0e6       # W/m2 at the tube outer surface (limit ~4.3 MW/m2, TiB2 thermal stress)
H_core = 1.0            # m, fuel column (active core)
pitch_over_d = 1.25     # triangular-ish square pitch / tube outer diameter
T_al_in, T_al_out = 1300.0, 1500.0
k_fuel, rho_fuel, cp_fuel, mu_fuel, beta_fuel = 45.0, 15600.0, 190.0, 4e-3, 6e-5   # APPROX liquid U-Pu


def main():
    r_out = r_fuel + t_metal + t_barrier
    A_per_pin = 2 * math.pi * r_out * H_core
    n_pins = P_TH / (q2_design * A_per_pin)
    V_fuel = n_pins * math.pi * r_fuel ** 2 * H_core
    q3 = P_TH / V_fuel
    pitch = pitch_over_d * 2 * r_out
    A_core = n_pins * pitch ** 2
    D_core = math.sqrt(4 * A_core / math.pi)
    f_fuel = math.pi * r_fuel ** 2 / pitch ** 2
    # fuel-to-wall drop in the pin: internally heated vertical cylinder, Nu = 0.34 Ra^0.226 on r (APPROX)
    nu, a = mu_fuel / rho_fuel, k_fuel / (rho_fuel * cp_fuel)
    Ra = M.G * beta_fuel * q3 * r_fuel ** 5 / (nu * a * k_fuel)
    h_in = max(0.34 * Ra ** 0.226, 1.0) * k_fuel / r_fuel
    q2_inner = q3 * r_fuel / 2
    dT_fuel = min(q2_inner / h_in, q3 * r_fuel ** 2 / (4 * k_fuel))
    # wall: Al side film from a liquid-metal correlation for the coolant channel
    al = props.coolants()["Al"]
    T_al = 0.5 * (T_al_in + T_al_out)
    D_h = 4 * (pitch ** 2 - math.pi * r_out ** 2) / (2 * math.pi * r_out)
    m_dot = P_TH / (al.cp(T_al) * (T_al_out - T_al_in))
    flow_area = n_pins * (pitch ** 2 - math.pi * r_out ** 2)
    v = m_dot / (al.rho(T_al) * flow_area)
    Pe = al.rho(T_al) * v * D_h / al.mu(T_al) * al.cp(T_al) * al.mu(T_al) / al.k(T_al)
    h_al = (4.82 + 0.0185 * Pe ** 0.827) * al.k(T_al) / D_h
    T_al_hot = T_al_out
    T_barrier_out = T_al_hot + q2_design / h_al
    T_metal_out = T_barrier_out + q2_design * t_barrier / M.BARRIERS["TiB2"]["k"]
    mat = M.MATERIALS["W-25Re"]
    T_wall_in = T_metal_out + q2_inner * r_fuel * math.log(r_out / r_fuel) / mat.k if False else T_metal_out + q2_design * t_metal / mat.k
    T_fuel_max = T_wall_in + dT_fuel
    # cap: Pb saturation pressure for a set of cap temperatures
    caps = {f"{Tc:.0f} K": M.vapour("Pb", Tc)["P_Pa"] / 1e5 for Tc in (2050.0, 2150.0, 2250.0, 2350.0)}
    w = M.wall(T_wall_in, q2_design, 3e5, r_out, t_metal, mat, "TiB2", t_barrier, h_al, T_al_hot)
    res = {"n_pins": n_pins, "pin_outer_radius_mm": r_out * 1e3, "fuel_m3": V_fuel, "fuel_t": V_fuel * rho_fuel / 1e3,
           "q3_fuel_MW_m3": q3 / 1e6, "core_diameter_m": D_core, "core_height_m": H_core, "core_m3": A_core * H_core,
           "fuel_fraction": f_fuel, "pitch_mm": pitch * 1e3, "q2_design_MW_m2": q2_design / 1e6,
           "h_fuel_side": h_in, "dT_fuel_K": dT_fuel, "h_al": h_al, "al_velocity_m_s": v, "al_m_dot_kg_s": m_dot,
           "T_al_in_K": T_al_in, "T_al_out_K": T_al_out, "T_barrier_al_face_K": T_barrier_out, "T_wall_inner_K": T_wall_in,
           "T_fuel_max_K": T_fuel_max, "pb_cap_pressure_bar": caps,
           "wall_check": {k: v for k, v in w.items()}}
    (HERE / "results" / "design.json").write_text(json.dumps(res, indent=1, default=str))
    for k, v in res.items():
        print(k, v if not isinstance(v, float) else round(v, 3))


if __name__ == "__main__":
    main()

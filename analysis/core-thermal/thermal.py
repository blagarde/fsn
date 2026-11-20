"""Steady-state heat path from fuel to coolant, and coolant hydraulics, for the core model.

Element geometries (the unit cell of the core lattice):
  slab | cylinder | sphere   fuel inside, wall around it, coolant outside (pins, plates, pebbles)
  annulus                    fuel outside a cooled tube, insulated cell boundary (A2/L7-type pool:
                             liquid fuel around coolant tubes); r_cell is set by the fuel fraction

Interfaces between fuel surface and wall: a contact conductance h_gap (W/m2 K; None = bonded),
or a radiative gap (L7 radiative coupling) with emissivities.

Liquid fuel conducts with k_eff = Nu_fuel * k (Nu_fuel = 1: pure conduction, the conservative
bound used for A2). Circulating fuel (fuel is the coolant) is handled in core.py.

Fuel conduction uses the conductivity integral, exact for T-dependent k and uniform source:
  integral_{Ts}^{Tmax} k dT = q''' * G, with G = a^2/2 (slab), a^2/4 (cylinder), a^2/6 (sphere),
  and G = [2 rc^2 ln(rc/rt) - rc^2 + rt^2] / 4 for the annulus.
Coolant film: liquid metals Nu = 4.82 + 0.0185 Pe^0.827; gases and salts Dittus-Boelter
(laminar Nu = 4.36 below Re 2300). Friction: Blasius / 64/Re. All APPROX correlations.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

SIGMA = 5.670374419e-8


@dataclass
class Cell:
    shape: str                 # slab | cylinder | sphere | annulus
    a: float                   # m: fuel half-thickness / radius; for annulus the tube outer radius
    wall_t: float              # m: wall (cladding / tube) thickness
    wall: object               # props.Solid
    fuel: object               # props.Solid
    h_gap: float | None = None # W/m2 K contact conductance; None = bonded
    radiative: tuple | None = None  # (eps_fuel_side, eps_wall_side) for a radiative gap
    nu_fuel: float = 1.0       # liquid-fuel convective enhancement of conduction


def geometry(cell: Cell, f_fuel: float, f_cool: float) -> dict:
    """Wall fraction, cell size, hydraulic diameter and heated surface per unit core volume."""
    a, t = cell.a, cell.wall_t
    if cell.shape == "annulus":
        # coolant inside tube radius ri = a - t; wall a-t..a; fuel a..rc. Per unit core volume:
        ri = a - t
        # f_cool = n_tubes * pi ri^2, f_wall = n_tubes * pi (a^2 - ri^2), f_fuel = n_tubes * pi (rc^2 - a^2)
        n = f_cool / (math.pi * ri * ri)                     # tubes per m2 of core cross-section
        f_wall = n * math.pi * (a * a - ri * ri)
        rc = math.sqrt(f_fuel / (n * math.pi) + a * a)
        return {"f_wall": f_wall, "r_cell": rc, "D_h": 2 * ri, "S_cool": n * 2 * math.pi * ri,
                "S_fuel": n * 2 * math.pi * a, "V_over_A_fuel": (rc * rc - a * a) / (2 * a),
                "G": (2 * rc * rc * math.log(rc / a) - rc * rc + a * a) / 4}
    m = {"slab": 1, "cylinder": 2, "sphere": 3}[cell.shape]
    ro = a + t
    f_wall = f_fuel * ((ro / a) ** m - 1)
    S_cool = (f_fuel + f_wall) * m / ro                      # wetted area per unit core volume
    return {"f_wall": f_wall, "r_cell": None, "D_h": 4 * f_cool / S_cool, "S_cool": S_cool,
            "S_fuel": f_fuel * m / a, "V_over_A_fuel": a / m, "G": a * a / (2 * m)}


def fuel_center_T(cell: Cell, q3_fuel: float, Ts: float, G: float) -> float:
    """Max fuel temperature from surface temperature Ts by the conductivity integral."""
    target = q3_fuel * G
    if target <= 0:
        return Ts
    T, acc = Ts, 0.0
    dT = 1.0
    while acc < target:
        k = cell.fuel.k(T + 0.5 * dT) * cell.nu_fuel
        if acc + k * dT >= target:
            return T + (target - acc) / k
        acc += k * dT
        T += dT
        if T > 2e4:
            return float("inf")
        dT = min(dT * 1.2, 20.0)
    return T


def wall_dT(cell: Cell, q2_fuel_surface: float, Tm: float) -> float:
    """Temperature drop across the wall, heat entering at the fuel side."""
    a, t, k = cell.a, cell.wall_t, cell.wall.k(Tm)
    if cell.shape == "slab":
        return q2_fuel_surface * t / k
    if cell.shape == "cylinder":
        return q2_fuel_surface * a * math.log((a + t) / a) / k
    if cell.shape == "sphere":
        return q2_fuel_surface * a * a * (1 / a - 1 / (a + t)) / k
    # annulus: heat enters the tube at outer radius a, leaves at inner radius a - t
    return q2_fuel_surface * a * math.log(a / (a - t)) / k


def gap_hot_T(cell: Cell, q2: float, T_wall_hot: float) -> float:
    """Fuel-surface temperature across the fuel/wall interface."""
    if cell.radiative:
        e1, e2 = cell.radiative
        return (T_wall_hot**4 + q2 * (1 / e1 + 1 / e2 - 1) / SIGMA) ** 0.25
    if cell.h_gap:
        return T_wall_hot + q2 / cell.h_gap
    return T_wall_hot


def film(coolant, T: float, v: float, D_h: float) -> tuple[float, float, float]:
    """(h W/m2K, Re, friction factor) for coolant at bulk T, velocity v, hydraulic diameter D_h."""
    rho, mu, k, cp = coolant.rho(T), coolant.mu(T), coolant.k(T), coolant.cp(T)
    Re = rho * v * D_h / mu
    Pr = cp * mu / k
    if coolant.kind == "liquid_metal":
        Nu = 4.82 + 0.0185 * (Re * Pr) ** 0.827
    else:
        Nu = 4.36 if Re < 2300 else 0.023 * Re**0.8 * Pr**0.4
    f = 64 / Re if Re < 2300 else 0.316 * Re**-0.25
    return Nu * k / D_h, Re, f


@dataclass
class ChannelResult:
    T_fuel_max: float
    T_fuel_surface_max: float
    T_wall_max: float
    T_out: float
    z_hot: float
    v: float
    Re: float
    h: float
    dp: float
    q2_wall_max: float


def hot_channel(cell: Cell, coolant, q3_core_avg: float, f_fuel: float, f_cool: float, H: float,
                T_in: float, T_out: float, F_radial: float, F_axial_shape="cosine",
                extrap: float = 0.1, orificed: bool = True, n_z: int = 60) -> ChannelResult:
    """Temperatures along the hottest channel of a core of active height H (m).

    q3_core_avg: core-average power density (W/m3 of core). Power density in the fuel is
    q3 / f_fuel. Axial shape: chopped cosine with extrapolation `extrap` x H at each end.
    Mass flux is set from the average channel (T_in -> T_out); if `orificed`, the hot channel's
    flow is raised in proportion to its power so its outlet equals T_out, else it heats F_radial
    times more.
    """
    g = geometry(cell, f_fuel, f_cool)
    He = H * (1 + 2 * extrap)
    zs = [(-0.5 + (i + 0.5) / n_z) * H for i in range(n_z)]
    shape = [math.cos(math.pi * z / He) for z in zs]
    avg_shape = sum(shape) / n_z
    peak_ax = 1 / avg_shape
    cpm = coolant.cp(0.5 * (T_in + T_out))
    # coolant mass flux (kg/s per m2 of coolant flow area) in the average channel
    G_avg = q3_core_avg * H / (cpm * (T_out - T_in) * f_cool)
    G_hot = G_avg * (F_radial if orificed else 1.0)
    Tb = 0.5 * (T_in + T_out)
    v = G_hot / coolant.rho(Tb)
    h, Re, f = film(coolant, Tb, v, g["D_h"])
    dp = f * H / g["D_h"] * coolant.rho(Tb) * v * v / 2
    best = None
    Tc = T_in
    Tw_max = q2_max = 0.0
    for z, s in zip(zs, shape):
        q3_local_core = q3_core_avg * F_radial * s / avg_shape
        dz = H / n_z
        Tc_mid = Tc + q3_local_core * dz * 0.5 / (G_hot * f_cool * cpm)
        Tc += q3_local_core * dz / (G_hot * f_cool * cpm)
        q3_fuel = q3_local_core / f_fuel
        q2_fuel = q3_fuel * g["V_over_A_fuel"]              # at the fuel surface
        q2_cool = q3_local_core / g["S_cool"]               # at the wetted surface
        Tw_cold = Tc_mid + q2_cool / h
        Tw_hot = Tw_cold
        for _ in range(3):
            Tw_hot = Tw_cold + wall_dT(cell, q2_fuel, 0.5 * (Tw_cold + Tw_hot))
        Ts = gap_hot_T(cell, q2_fuel, Tw_hot)
        Tf = fuel_center_T(cell, q3_fuel, Ts, g["G"])
        if best is None or Tf > best[0]:
            best = (Tf, Ts, Tw_hot, z, q2_cool)
        Tw_max = max(Tw_max, Tw_hot)
        q2_max = max(q2_max, q2_cool)
    return ChannelResult(T_fuel_max=best[0], T_fuel_surface_max=best[1], T_wall_max=Tw_max,
                         T_out=Tc, z_hot=best[3], v=v, Re=Re, h=h, dp=dp, q2_wall_max=q2_max)

"""Coupled steady state: criticality (neutronics.py) + heat path (thermal.py) -> power and flow.

The physics the model encodes:
  * Fissile density does not set the power of a critical reactor. It sets the critical size and
    inventory, and the flux needed per watt (phi = q''' / (E_f Sigma_f)).
  * Power is limited by heat removal: the hottest point of the fuel (or the hottest wall) must stay
    below its limit, so q'''_max follows from the heat path, and P_max = q'''_max * V_core.
  * The coolant must carry P away: m_dot = P / (cp (T_out - T_in)); its velocity, pressure drop
    and pumping power follow from the lattice.
  * Temperature then settles where the reactivity feedbacks balance the control state; those
    coefficients (Doppler, fuel and coolant density) come out of the same one-group model and
    feed the transient model (kinetics.py).

Geometry: a cylinder of fixed H/D, homogenised, optionally reflected. Reflector savings come
from the two-region sphere of the same composition and are applied to the cylinder.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict

from scipy.special import j1

import neutronics as N
import props as P
import thermal as TH

COOLANT_MAT = {"Na": "Na", "Pb": "Pb", "Al": "Al", "He70": "He", "FLiBe": "FLiBe"}
WALL_MAT = {"W": ("W", 19.0), "Mo": ("Mo", 10.0), "SiC": ("SiC", 3.21), "steel": ("steel", 7.6), "AlN": ("AlN", 3.26)}
YEAR = 3.15576e7


@dataclass
class CoreSpec:
    name: str
    fuel: str = "UPuN"              # props.fuels() key
    pu: float = 0.15                # Pu / heavy metal (atom)
    f_fuel: float = 0.40            # fuel volume fraction of the core
    f_other: float = 0.0            # other structure (wrappers, grids), taken as wall material
    coolant: str = "Pb"             # props.coolants() key
    shape: str = "cylinder"         # cell shape: slab | cylinder | sphere | annulus
    a_mm: float = 3.0               # fuel radius / half-thickness (annulus: tube outer radius)
    wall_mm: float = 0.5
    wall: str = "steel"
    h_gap: float | None = None      # W/m2 K; None = bonded
    radiative: tuple | None = None  # (eps_fuel, eps_wall)
    nu_fuel: float = 1.0
    circulating: bool = False       # fuel is the coolant (no cell); loop/core volume ratio below
    loop_to_core_volume: float = 1.0
    T_in: float = 1173.0            # K
    T_out: float = 1373.0           # K
    h_over_d: float = 1.0
    reflector: tuple | None = ("steel", 7.6, 30.0)   # (material, g/cc, thickness cm) or None
    F_radial: float | None = None   # None: unzoned fundamental mode; or a design value (zoned core)
    T_fuel_limit: float | None = None  # default: fuel limit - 100 K
    T_wall_limit: float | None = None  # default: wall limit - 300 K (creep margin, APPROX)
    v_max: float = 10.0             # m/s; liquid metals ~2-10, gases ~50-100
    orificed: bool = True
    q3_cap_MW_m3: float | None = None  # optional power-density cap (circulating fuel: required, default 300)
    notes: str = ""


def _fluid(spec):
    return P.coolants()[spec.coolant]


def _fuel(spec):
    return P.fuels()[spec.fuel]


def _wall(spec):
    return P.walls()[spec.wall]


def fractions(spec) -> dict:
    """Volume fractions fuel / wall / coolant / other and the cell geometry."""
    if spec.circulating:
        return {"f_fuel": spec.f_fuel, "f_wall": 0.0, "f_cool": 0.0, "f_other": 1 - spec.f_fuel, "geom": None}
    cell = make_cell(spec)
    rest = 1 - spec.f_fuel - spec.f_other
    if spec.shape == "annulus":
        a, ri = spec.a_mm / 1e3, (spec.a_mm - spec.wall_mm) / 1e3
        f_cool = rest * ri * ri / (a * a)
    else:
        f_wall = TH.geometry(cell, spec.f_fuel, 0.1)["f_wall"]
        f_cool = rest - f_wall
    if f_cool <= 0.02:
        raise ValueError(f"{spec.name}: no room for coolant (fuel {spec.f_fuel}, other {spec.f_other})")
    g = TH.geometry(cell, spec.f_fuel, f_cool)
    return {"f_fuel": spec.f_fuel, "f_wall": g["f_wall"], "f_cool": f_cool, "f_other": spec.f_other, "geom": g}


def make_cell(spec) -> TH.Cell:
    return TH.Cell(spec.shape, spec.a_mm / 1e3, spec.wall_mm / 1e3, _wall(spec), _fuel(spec),
                   spec.h_gap, spec.radiative, spec.nu_fuel)


def region(spec, T_fuel, T_cool, fuel_density_factor=1.0, cool_density_factor=1.0) -> N.Region:
    fr = fractions(spec)
    fuel = _fuel(spec)
    r = N.Region()
    r.add("fuel", N.fuel_material(spec.fuel, spec.pu, fuel.rho / 1e3 * fuel_density_factor), fr["f_fuel"], T_fuel)
    if spec.circulating:
        wm, wr = WALL_MAT[spec.wall]
        if fr["f_other"] > 0:
            r.add("wall", N.element_material(wm, wr), fr["f_other"], T_cool)
    else:
        cool = _fluid(spec)
        r.add("coolant", N.element_material(COOLANT_MAT[spec.coolant], cool.rho(T_cool) / 1e3 * cool_density_factor),
              fr["f_cool"], T_cool)
        wm, wr = WALL_MAT[spec.wall]
        if fr["f_wall"] + fr["f_other"] > 0:
            r.add("wall", N.element_material(wm, wr), fr["f_wall"] + fr["f_other"], T_cool)
    return r


def _refl(spec, T):
    if not spec.reflector:
        return None, 0.0
    mat, rho, t = spec.reflector
    r = N.Region().add("reflector", N.element_material(mat, rho), 1.0, T)
    return N.one_group(r), t


def criticality(spec, T_fuel, T_cool) -> dict:
    g = N.one_group(region(spec, T_fuel, T_cool))
    if g.k_inf <= 1:
        return {"critical": False, "g": g}
    B = math.sqrt((g.k_inf - 1) / g.M2)
    refl, t = _refl(spec, T_cool)
    Rs = N.reflected_sphere_radius(g, refl, t) if refl else N.bare_sphere_radius(g)
    delta = math.pi / B - Rs          # reflector savings incl. extrapolation (cm)
    # cylinder with the same savings: (2.405/(R+delta))^2 + (pi/(H+2 delta))^2 = B^2
    lo, hi = 1.0, 1e5
    for _ in range(200):
        R = math.sqrt(lo * hi)
        Bg2 = (2.405 / (R + delta)) ** 2 + (math.pi / (2 * R * spec.h_over_d + 2 * delta)) ** 2
        lo, hi = (R, hi) if Bg2 > B * B else (lo, R)
    R = lo
    H = 2 * R * spec.h_over_d
    x = 2.405 * R / (R + delta)
    F_r_mode = x / (2 * j1(x))
    return {"critical": True, "g": g, "R_cm": R, "H_cm": H, "V_m3": math.pi * (R / 100) ** 2 * H / 100,
            "delta_cm": delta, "R_sphere_cm": Rs, "F_r_mode": F_r_mode, "B2": B * B}


def savings_cm(g: N.OneGroup, refl: N.OneGroup | None, t: float) -> float:
    """Reflector savings incl. extrapolation, one-group slab formula (large cores):
    delta = (D_c/D_r) L_r tanh(T/L_r) + 2.13 D_c (bare: 2.13 D_c)."""
    if refl is None:
        return 2.13 * g.D
    L_r = math.sqrt(refl.D / max(refl.sig_a - refl.nu_sig_f, 1e-12))
    return g.D / refl.D * L_r * math.tanh(t / L_r) + 2.13 * g.D


def at_geometry(spec, R_cm, H_cm, T_fuel, T_cool) -> dict:
    """Same keys as criticality() for a cylinder of given size; adds k_eff."""
    g = N.one_group(region(spec, T_fuel, T_cool))
    refl, t = _refl(spec, T_cool)
    d = savings_cm(g, refl, t)
    Bg2 = (2.405 / (R_cm + d)) ** 2 + (math.pi / (H_cm + 2 * d)) ** 2
    x = 2.405 * R_cm / (R_cm + d)
    return {"critical": True, "g": g, "R_cm": R_cm, "H_cm": H_cm, "V_m3": math.pi * (R_cm / 100) ** 2 * H_cm / 100,
            "delta_cm": d, "F_r_mode": x / (2 * j1(x)), "B2": Bg2, "k_eff": g.nu_sig_f / (g.sig_a + g.D * Bg2)}


def k_eff(spec, crit, T_fuel, T_cool, fuel_df=1.0, cool_df=1.0, H_factor=1.0) -> float:
    """k_eff at the critical geometry (savings held fixed) for perturbed temperatures/densities."""
    g = N.one_group(region(spec, T_fuel, T_cool, fuel_df, cool_df))
    R, H, d = crit["R_cm"], crit["H_cm"] * H_factor, crit["delta_cm"]
    Bg2 = (2.405 / (R + d)) ** 2 + (math.pi / (H + 2 * d)) ** 2
    return g.nu_sig_f / (g.sig_a + g.D * Bg2)


def delayed_retention(beta, lam, tau_core, tau_loop):
    """Fraction of each delayed group emitted in the core for circulating fuel (slug flow, flat importance)."""
    out = []
    for l in lam:
        if l <= 0:
            out.append(1.0)
            continue
        e_c, e_l = math.exp(-l * tau_core), math.exp(-l * tau_loop)
        c0 = (1 - e_c) * e_l / (1 - e_c * e_l)
        out.append(1 - (1 - e_c) * (1 - c0) / (l * tau_core))
    return out


def decay_heat_fraction(t_s: float, T_op_s: float = 2 * YEAR) -> float:
    """Way-Wigner decay heat after shutdown, fraction of operating power. APPROX (+-30-50 %);
    replace with ANS-5.1 / ENDF decay data (open question)."""
    t = max(t_s, 1.0)
    return 0.0622 * (t**-0.2 - (t + T_op_s) ** -0.2)


@dataclass
class Steady:
    spec: dict
    critical: bool
    k_inf: float
    cr_core: float
    moderating_weights: dict
    note: str
    k_eff: float = 1.0
    pu: float = 0.0
    R_m: float = 0.0
    H_m: float = 0.0
    V_m3: float = 0.0
    fissile_kg_m3: float = 0.0
    fissile_kg: float = 0.0
    hm_kg: float = 0.0
    fractions: dict = field(default_factory=dict)
    F_radial: float = 0.0
    q3_max_MW_m3: float = 0.0
    limit: str = ""
    P_MW: float = 0.0
    specific_power_kW_kg_fissile: float = 0.0
    flux_avg_n_cm2_s: float = 0.0
    fast_fluence_per_fpy: float = 0.0
    m_dot_kg_s: float = 0.0
    vol_flow_m3_s: float = 0.0
    velocity_m_s: float = 0.0
    dp_core_bar: float = 0.0
    pumping_core_MW: float = 0.0
    T_fuel_max_K: float = 0.0
    T_wall_max_K: float = 0.0
    q2_wall_max_MW_m2: float = 0.0
    T_fuel_avg_K: float = 0.0
    beta_eff: float = 0.0
    beta_retained: float = 1.0
    gen_time_s: float = 0.0
    beta: list = field(default_factory=list)
    lam: list = field(default_factory=list)
    doppler_K_D_pcm: float = 0.0          # T dk/dT -> pcm per unit ln T
    fuel_density_pcm_per_K: float = 0.0
    coolant_density_pcm_per_K: float = 0.0
    coolant_void_pcm: float = 0.0
    heat_capacity_core_MJ_K: float = 0.0
    fuel_heat_capacity_MJ_K: float = 0.0
    coolant_heat_capacity_MJ_K: float = 0.0
    R_fuel_to_coolant_K_per_MW: float = 0.0
    adiabatic_rate_K_s: float = 0.0
    decay_MW: dict = field(default_factory=dict)
    adiabatic_after_scram_s_to_limit: float = 0.0


def solve(spec: CoreSpec, P_MW: float | None = None, geometry: tuple | None = None) -> Steady:
    """Critical size, then the max power the heat path allows (or the temperatures at P_MW).
    geometry=(R_cm, H_cm) fixes the core size instead (k_eff is then reported, not forced to 1)."""
    fuel, cool = _fuel(spec), (None if spec.circulating else _fluid(spec))
    T_lim_f = spec.T_fuel_limit or fuel.T_limit - 100.0
    T_lim_w = spec.T_wall_limit or (_wall(spec).T_limit - 300.0 if not spec.circulating else 1e9)
    T_cool = 0.5 * (spec.T_in + spec.T_out)
    T_fuel = T_cool + 150.0
    fr = fractions(spec)
    for _ in range(4):  # iterate fuel temperature <-> critical size
        c = at_geometry(spec, *geometry, T_fuel, T_cool) if geometry else criticality(spec, T_fuel, T_cool)
        g = c["g"]
        res = Steady(spec=asdict(spec), critical=c["critical"], k_inf=g.k_inf, cr_core=g.cr,
                     k_eff=c.get("k_eff", 1.0), pu=spec.pu,
                     moderating_weights=g.weights, note=g.note, fractions={k: v for k, v in fr.items() if k != "geom"})
        if not c["critical"]:
            return res
        V = c["V_m3"]
        F_r = spec.F_radial or c["F_r_mode"]
        H = c["H_cm"] / 100
        extrap = c["delta_cm"] / c["H_cm"]
        if spec.circulating:
            q3 = P_MW * 1e6 / V if P_MW else (spec.q3_cap_MW_m3 or 300.0) * 1e6
            limit = "given power" if P_MW else f"power-density cap {(spec.q3_cap_MW_m3 or 300.0):.0f} MW/m3"
            break
        cell = make_cell(spec)

        def channel(q3):
            return TH.hot_channel(cell, cool, q3, fr["f_fuel"], fr["f_cool"], H, spec.T_in, spec.T_out,
                                  F_r, extrap=extrap, orificed=spec.orificed)
        if P_MW:
            q3 = P_MW * 1e6 / V
            limit = "given power"
        else:
            # velocity limit is linear in q3: v = G/rho, G = q3 H / (cp dT f_cool) * F_r(orificed)
            ch1 = channel(1e6)
            q3_v = 1e6 * spec.v_max / ch1.v
            lo, hi = 1e3, q3_v
            ok = lambda q: (lambda r: r.T_fuel_max <= T_lim_f and r.T_wall_max <= T_lim_w)(channel(q))
            if spec.q3_cap_MW_m3 and spec.q3_cap_MW_m3 * 1e6 < hi and ok(spec.q3_cap_MW_m3 * 1e6):
                q3, limit = spec.q3_cap_MW_m3 * 1e6, f"power-density cap {spec.q3_cap_MW_m3:.0f} MW/m3"
            elif ok(hi):
                q3, limit = hi, f"coolant velocity {spec.v_max} m/s"
            else:
                for _ in range(40):
                    mid = math.sqrt(lo * hi)
                    lo, hi = (mid, hi) if ok(mid) else (lo, mid)
                q3 = lo
                r = channel(q3 * 1.01)
                limit = (f"fuel {T_lim_f:.0f} K" if r.T_fuel_max > T_lim_f else f"wall {T_lim_w:.0f} K")
        ch = channel(q3)
        # average fuel temperature (APPROX): coolant mean + mean film/wall/gap rise + 1/2 the mean fuel rise
        rise_hot = ch.T_fuel_max - (spec.T_in + 0.5 * (spec.T_out - spec.T_in))
        T_new = T_cool + rise_hot / (F_r * 1.2) * 0.75
        if abs(T_new - T_fuel) < 5:
            T_fuel = T_new
            break
        T_fuel = T_new

    res.R_m, res.H_m, res.V_m3 = c["R_cm"] / 100, c["H_cm"] / 100, V
    res.fissile_kg_m3 = g.fissile_kg_m3
    res.fissile_kg, res.hm_kg = g.fissile_kg_m3 * V, g.hm_kg_m3 * V
    res.F_radial = F_r
    res.T_fuel_avg_K = T_fuel
    res.beta, res.lam, res.gen_time_s = g.beta, g.lam, g.gen_time

    if spec.circulating:
        res.limit = limit
        cpf = fuel.cp(T_cool)
        m_dot = q3 * V / (cpf * (spec.T_out - spec.T_in))
        mass_core = fuel.rho * V * spec.f_fuel
        tau_c = mass_core / m_dot
        keep = delayed_retention(g.beta, g.lam, tau_c, tau_c * spec.loop_to_core_volume)
        res.beta_retained = sum(b * k for b, k in zip(g.beta, keep)) / sum(g.beta)
        res.m_dot_kg_s, res.vol_flow_m3_s = m_dot, m_dot / fuel.rho
        res.T_fuel_max_K = spec.T_out
        res.velocity_m_s = float("nan")
    else:
        res.limit = limit
        res.T_fuel_max_K, res.T_wall_max_K = ch.T_fuel_max, ch.T_wall_max
        res.q2_wall_max_MW_m2 = ch.q2_wall_max / 1e6
        cpm = cool.cp(T_cool)
        res.m_dot_kg_s = q3 * V / (cpm * (spec.T_out - spec.T_in))
        res.vol_flow_m3_s = res.m_dot_kg_s / cool.rho(T_cool)
        res.velocity_m_s, res.dp_core_bar = ch.v, ch.dp / 1e5
        res.pumping_core_MW = res.vol_flow_m3_s * ch.dp / 1e6
    res.q3_max_MW_m3 = q3 / 1e6
    res.P_MW = q3 * V / 1e6
    res.specific_power_kW_kg_fissile = res.P_MW * 1e3 / res.fissile_kg
    q3_cm3 = q3 / 1e6  # W/cm3
    res.flux_avg_n_cm2_s = q3_cm3 / (g.J_per_fission_rate * g.sig_f)
    res.fast_fluence_per_fpy = res.flux_avg_n_cm2_s * YEAR
    res.beta_eff = g.beta_eff * res.beta_retained

    # reactivity coefficients at the critical geometry (finite differences)
    rho = lambda k: 1e5 * (k - 1) / k
    k0 = k_eff(spec, c, T_fuel, T_cool)
    kD = k_eff(spec, c, T_fuel * 1.2, T_cool)
    res.doppler_K_D_pcm = (rho(kD) - rho(k0)) / math.log(1.2)
    dT = 100.0
    df = 1 / (1 + 3 * fuel.alpha_lin * dT)
    if fuel.liquid:   # pool level rises: same fuel mass over a taller core
        kf = k_eff(spec, c, T_fuel, T_cool, fuel_df=df, H_factor=1 / df)
    else:             # solid fuel: density falls at fixed core size (axial growth not credited)
        kf = k_eff(spec, c, T_fuel, T_cool, fuel_df=df)
    res.fuel_density_pcm_per_K = (rho(kf) - rho(k0)) / dT
    if not spec.circulating:
        cdf = cool.rho(T_cool + dT) / cool.rho(T_cool)
        res.coolant_density_pcm_per_K = (rho(k_eff(spec, c, T_fuel, T_cool, cool_df=cdf)) - rho(k0)) / dT
        res.coolant_void_pcm = rho(k_eff(spec, c, T_fuel, T_cool, cool_df=1e-6)) - rho(k0)

    # heat capacities and lumped resistances for kinetics.py
    wall = _wall(spec)
    C_f = fuel.rho * fuel.cp(T_fuel) * spec.f_fuel * V
    C_w = wall.rho * wall.cp(T_cool) * (fr["f_wall"] + fr["f_other"]) * V
    C_c = 0.0 if spec.circulating else cool.rho(T_cool) * cool.cp(T_cool) * fr["f_cool"] * V
    res.fuel_heat_capacity_MJ_K = C_f / 1e6
    res.coolant_heat_capacity_MJ_K = (C_c + C_w) / 1e6
    res.heat_capacity_core_MJ_K = (C_f + C_w + C_c) / 1e6
    res.R_fuel_to_coolant_K_per_MW = (T_fuel - T_cool) / res.P_MW
    res.adiabatic_rate_K_s = res.P_MW / res.heat_capacity_core_MJ_K
    res.decay_MW = {lbl: res.P_MW * decay_heat_fraction(t) for lbl, t in
                    (("1 s", 1), ("1 min", 60), ("1 h", 3600), ("1 day", 86400), ("30 days", 30 * 86400))}
    # loss of all cooling after scram: time for the core inventory to reach the fuel limit on decay heat
    E_needed = res.heat_capacity_core_MJ_K * (T_lim_f - T_fuel)
    t, E = 1.0, 0.0
    while E < E_needed and t < 1e8:
        dt = t * 0.05
        E += res.P_MW * decay_heat_fraction(t) * dt
        t += dt
    res.adiabatic_after_scram_s_to_limit = t
    return res


def solve_for_power(spec: CoreSpec, P_target_MW: float, k_target: float = 1.0, iters: int = 4) -> Steady:
    """Design mode: size the core for P_target at the heat-path limit, then find the Pu fraction
    that makes that core critical (k_eff = k_target; > 1 leaves margin for burnup and control).

    Iterates because the power-density limit depends on core height and radial peaking.
    """
    import dataclasses
    st = solve(spec)
    if not st.critical:
        return st
    q3 = st.q3_max_MW_m3
    s = spec
    for _ in range(iters):
        V = P_target_MW / q3
        R = (V / (2 * math.pi * s.h_over_d)) ** (1 / 3) * 100
        H = 2 * R * s.h_over_d
        T_cool = 0.5 * (s.T_in + s.T_out)
        T_fuel = st.T_fuel_avg_K
        lo, hi = 0.02, 0.8
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            k = at_geometry(dataclasses.replace(s, pu=mid), R, H, T_fuel, T_cool)["k_eff"]
            lo, hi = (mid, hi) if k < k_target else (lo, mid)
        s = dataclasses.replace(s, pu=0.5 * (lo + hi))
        st = solve(s, geometry=(R, H))
        if abs(st.q3_max_MW_m3 - q3) / q3 < 0.01:
            break
        q3 = st.q3_max_MW_m3
    # report at the target power (the limit may now sit slightly above it)
    return solve(s, P_MW=P_target_MW, geometry=(R, H)) if not s.circulating else st

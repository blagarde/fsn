"""Simple configurations of molten U-Pu: how much heat does it make, and how hot does it get?

A body of liquid U-Pu metal (slab, sphere or cylinder; any size and Pu assay; bare or reflected)
is held at a temperature where it is exactly critical. Because the temperature coefficient is
negative (Doppler + thermal expansion), the body finds that temperature by itself:
  * colder than that -> supercritical -> power rises -> it heats up;
  * hotter -> subcritical -> power falls -> it cools.
So the steady power is whatever the heat-removal path carries away at the critical temperature.
The program finds that self-regulated equilibrium:

  P* such that  k_eff( temperatures produced by P* with the chosen heat removal ) = 1

and reports power, temperatures, heat flux, inventory and the feedback coefficients. If the body
is subcritical even when cold it makes no fission power; if it is still supercritical at the
temperature limit (boiling, default 3,500 K), there is no safe equilibrium ("runaway").

Heat removal options (surface ones apply to the cooled faces only; the rest are insulated):
  adiabatic                 nothing removed: the body heats to the critical temperature, then P -> 0
  convective  h, T_c        q'' = h (T_s - T_c)        (liquid-metal or gas coolant on the face)
  radiative   eps, T_sink   q'' = sigma eps (T_s^4 - T_sink^4)   (radiation to a cold wall, L7-like)
  immersed    UA, T_c       Q = UA (T_mean - T_c)       (cooling tubes spread through the liquid)
Inside the liquid: conduction with k_eff = Nu * k, or "mixed" (isothermal liquid, Nu -> inf).

Thermal expansion keeps the mass fixed: a slab in a container of fixed area gets thicker, a
cylinder of fixed radius gets taller, a sphere grows freely. Note the slab result: thickness x
density stays constant, so for a wide slab the expansion feedback nearly cancels; Doppler does the work.

Neutronics: one-group diffusion (neutronics.py) with OpenMC-collapsed constants; extrapolation
distance 2.13 D, or one-group reflector savings. Diffusion overstates leakage in small bare
metal bodies (see validate.py: Godiva); pool.py --check runs OpenMC on the same body to show the error.

Run:  /opt/mamba/envs/nuc/bin/python pool.py --shape slab --size 30 --pu 0.15 --removal convective --h 20000 --Tc 1500
      /opt/mamba/envs/nuc/bin/python pool.py scan --shape slab --pu 0.10 0.15 0.20 --size 10 20 30 40 60 --removal radiative
      /opt/mamba/envs/nuc/bin/python pool.py transient --shape sphere --size 20 --pu 0.2 --removal adiabatic
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, asdict, field
from pathlib import Path

import numpy as np

import neutronics as N
import props as P

SIGMA = 5.670374419e-8
OUT = Path(__file__).resolve().parent / "results"

# Liquid U-Pu (APPROX, U-rich alloys): rho = 17.2 g/cc at 1,408 K, -1.0e-3 g/cc per K
# (liquid-U handbook range, IAEA thermophysical properties 2008); k 40 W/m K; cp 190 J/kg K.
RHO_REF, T_REF, DRHO_DT = 17.2, 1408.0, -1.0e-3
K_LIQ, CP_LIQ = 40.0, 190.0
T_SOLIDUS = 1350.0   # APPROX: U-rich U-Pu liquidus ~1,350-1,400 K; a surface below this freezes (crust)


def rho_gcc(T):
    return RHO_REF + DRHO_DT * (T - T_REF)


@dataclass
class Body:
    shape: str = "slab"          # slab | sphere | cylinder
    size_cm: float = 30.0        # slab thickness, sphere radius, cylinder radius (at T_ref density)
    height_cm: float = 0.0       # cylinder height (0 -> 2 x radius)
    width_cm: float = 0.0        # slab lateral side (square); 0 -> effectively infinite (1e4 cm)
    pu: float = 0.15             # Pu / (U + Pu) atom fraction (reactor-grade vector, depleted U)
    reflector: tuple | None = None   # (material, g/cc, thickness cm), e.g. ("W", 19.0, 20)
    removal: str = "convective"  # adiabatic | convective | radiative | immersed
    h: float = 2.0e4             # W/m2 K
    eps: float = 0.8
    UA: float = 1.0e6            # W/K (immersed)
    T_c: float = 1500.0          # K: coolant / sink temperature
    faces: int = 2               # slab: cooled faces (1 or 2); cylinder: 1 = side only, 2 = side + ends
    nu: float = 1.0              # conduction enhancement in the liquid (Nu); 0 -> fully mixed
    T_limit: float = 3500.0      # K: boiling / vapour limit (APPROX)
    k_scale: float = 1.0         # set by solve(transport=True): OpenMC k / model k at the cold state


# --------------------------------------------------------------------------- geometry
def dims(b: Body, T_mean: float) -> dict:
    """Dimensions (cm) at mean temperature T_mean, mass fixed (expansion direction per shape)."""
    s = rho_gcc(T_REF) / rho_gcc(T_mean)          # volume ratio
    if b.shape == "slab":
        W = b.width_cm or 1e4
        return {"t": b.size_cm * s, "W": W, "V_cm3": b.size_cm * s * W * W,
                "A_cool_cm2": b.faces * W * W}
    if b.shape == "sphere":
        R = b.size_cm * s ** (1 / 3)
        return {"R": R, "V_cm3": 4 / 3 * math.pi * R**3, "A_cool_cm2": 4 * math.pi * R * R}
    H0 = b.height_cm or 2 * b.size_cm
    H = H0 * s
    R = b.size_cm
    A = 2 * math.pi * R * H + (2 * math.pi * R * R if b.faces == 2 else 0.0)
    return {"R": R, "H": H, "V_cm3": math.pi * R * R * H, "A_cool_cm2": A}


CALIBRATION = OUT / "pool_calibration.json"


def _cal() -> tuple[float, float]:
    """(leakage factor f, extrapolation coefficient c) fitted to OpenMC by `pool.py calibrate`;
    (1, 2.13) = plain one-group diffusion if no calibration exists for the current constants."""
    try:
        d = json.loads(CALIBRATION.read_text())
        if d.get("constants") == str(N.CONSTANTS):
            return d["f"], d["c"]
    except (OSError, ValueError, KeyError):
        pass
    return 1.0, 2.13


def extrap(b: Body, g: N.OneGroup) -> float:
    if not b.reflector:
        return _cal()[1] * g.D
    import core
    mat, rho, t = b.reflector
    r = N.one_group(N.Region().add("reflector", N.element_material(mat, rho), 1.0, max(b.T_c, 900.0)))
    return core.savings_cm(g, r, t)


def buckling(b: Body, d: dict, delta: float) -> float:
    if b.shape == "slab":
        return (math.pi / (d["t"] + 2 * delta)) ** 2 + 2 * (math.pi / (d["W"] + 2 * delta)) ** 2
    if b.shape == "sphere":
        return (math.pi / (d["R"] + delta)) ** 2
    return (2.405 / (d["R"] + delta)) ** 2 + (math.pi / (d["H"] + 2 * delta)) ** 2


def one_group(b: Body, T_doppler: float, T_mean: float) -> N.OneGroup:
    m = N.fuel_material("UPu_liquid", b.pu, rho_gcc(T_mean))
    return N.one_group(N.Region().add("fuel", m, 1.0, T_doppler))


def k_eff(b: Body, T_doppler: float, T_mean: float) -> tuple[float, N.OneGroup, dict, float]:
    g = one_group(b, T_doppler, T_mean)
    d = dims(b, T_mean)
    delta = extrap(b, g)
    B2 = buckling(b, d, delta)
    return b.k_scale * g.nu_sig_f / (g.sig_a + _cal()[0] * g.D * B2), g, d, delta


# --------------------------------------------------------------------------- temperatures
def profile(b: Body, d: dict, delta: float, P_W: float, n: int = 200) -> dict:
    """1D steady temperature in the liquid for total power P_W with the fundamental-mode source.

    Slab: coordinate across the thickness; sphere and cylinder: radius (cylinder ends insulated
    in the 1D model; with faces=2 their area is added to the boundary conductance). Returns mean,
    power-weighted mean (for Doppler), max and surface temperatures.
    """
    V = d["V_cm3"] * 1e-6
    if b.shape == "slab":
        L = d["t"] / 100
        x = np.linspace(-L / 2, L / 2, n)
        te = (d["t"] + 2 * delta) / 100
        src = np.cos(math.pi * x / te)
        w = np.ones_like(x)                  # volume weight per node (planar)
        geom = "planar"
    else:
        R = d["R"] / 100
        x = np.linspace(0, R, n)
        if b.shape == "sphere":
            Bn = math.pi / (R + delta / 100)
            src = np.sinc(Bn * x / math.pi)
            w = x * x
            geom = "spherical"
        else:
            from scipy.special import j0
            src = j0(2.405 * x / (R + delta / 100))
            w = x
            geom = "cylindrical"
    q3 = src * P_W / (V * (np.trapezoid(src * w, x) / np.trapezoid(w, x)))   # W/m3, mean = P/V
    A_cool = d["A_cool_cm2"] * 1e-4

    def surface_T(Q):
        if b.removal == "adiabatic" or Q <= 0:
            return None
        q2 = Q / A_cool
        if b.removal == "convective":
            return b.T_c + q2 / b.h
        if b.removal == "radiative":
            return (b.T_c**4 + q2 / (SIGMA * b.eps)) ** 0.25
        return None

    k_l = K_LIQ * (b.nu if b.nu > 0 else 1.0)
    if b.removal == "immersed" or b.nu == 0:
        # isothermal liquid (tubes everywhere, or full mixing): mean set by the boundary/UA law
        if b.removal == "immersed":
            Tm = b.T_c + P_W / b.UA
        elif b.removal == "adiabatic":
            Tm = None
        else:
            Tm = surface_T(P_W)
        return {"T_mean": Tm, "T_pw": Tm, "T_max": Tm, "T_s": Tm, "q2_MW_m2": P_W / A_cool / 1e6 if A_cool else 0.0}
    if b.removal == "adiabatic":
        return {"T_mean": None, "T_pw": None, "T_max": None, "T_s": None, "q2_MW_m2": 0.0}
    # conduction: integrate heat flux outward, then temperature inward from the surface
    if geom == "planar" and b.faces == 2:
        # symmetric: solve the half from the insulated mid-plane to one cooled face
        keep = x >= 0
        x, q3, w = x[keep] - x[keep][0], q3[keep], w[keep]
    if geom == "planar":
        area = np.ones_like(x)
    elif geom == "spherical":
        area = x * x
    else:
        area = x
    # heat generated inside x (per unit of the shape's area measure), then flux and temperature drop
    gen = np.concatenate([[0.0], np.cumsum(0.5 * (q3[1:] * w[1:] + q3[:-1] * w[:-1]) * np.diff(x))])
    flux = np.divide(gen, area, out=np.zeros_like(gen), where=area > 0)   # W/m2
    Ts = surface_T(P_W)
    seg = 0.5 * (flux[1:] + flux[:-1]) * np.diff(x) / k_l
    T = Ts + np.concatenate([np.cumsum(seg[::-1])[::-1], [0.0]])
    xx, qq, ww = x, q3, w
    Tmean = float(np.trapezoid(T * ww, xx) / np.trapezoid(ww, xx))
    Tpw = float(np.trapezoid(T * qq * ww, xx) / np.trapezoid(qq * ww, xx))
    return {"T_mean": Tmean, "T_pw": Tpw, "T_max": float(T.max()), "T_s": float(Ts),
            "q2_MW_m2": P_W / A_cool / 1e6}


# --------------------------------------------------------------------------- equilibrium
@dataclass
class Result:
    body: dict
    status: str
    P_MW: float = 0.0
    power_density_MW_m3: float = 0.0
    k_cold: float = 0.0
    T_crit_K: float = 0.0          # power-weighted temperature at which k_eff = 1
    T_mean_K: float = 0.0
    T_max_K: float = 0.0
    T_surface_K: float = 0.0
    q2_surface_MW_m2: float = 0.0
    dims_cm: dict = field(default_factory=dict)
    mass_t: float = 0.0
    pu_fissile_kg: float = 0.0
    alpha_doppler_pcm_K: float = 0.0
    alpha_expansion_pcm_K: float = 0.0
    alpha_total_pcm_K: float = 0.0
    excess_at_limit_pcm: float = 0.0
    feedback_to_limit_pcm: float = 0.0   # reactivity feedback from cold to the temperature limit (negative)
    beta_eff: float = 0.0
    gen_time_s: float = 0.0
    flux_n_cm2_s: float = 0.0
    note: str = ""


def coefficients(b: Body, T: float) -> tuple[float, float]:
    """(Doppler, expansion) reactivity coefficients in pcm/K at uniform temperature T."""
    rho = lambda k: 1e5 * (k - 1) / k
    dT = 50.0
    k0 = k_eff(b, T, T)[0]
    kD = k_eff(b, T + dT, T)[0]
    kE = k_eff(b, T, T + dT)[0]
    return (rho(kD) - rho(k0)) / dT, (rho(kE) - rho(k0)) / dT


OPENMC_CACHE = OUT / "pool_openmc_cache.json"


def anchor(b: Body, T0: float) -> float:
    """OpenMC k_eff / model k_eff at the cold state (cached on disk by body geometry and assay)."""
    import dataclasses
    key = json.dumps([b.shape, round(b.size_cm, 3), b.width_cm, b.height_cm, b.pu, b.reflector, round(T0, 1), b.T_c, "hi-stat"])
    try:
        cache = json.loads(OPENMC_CACHE.read_text())
    except (OSError, ValueError):
        cache = {}
    if key not in cache:
        r = openmc_keff(dataclasses.replace(b, k_scale=1.0), T0, particles=40000, batches=90, inactive=20)
        cache[key] = r["openmc_k"]
        cache[key + "|sd"] = r["openmc_sd"]
        OPENMC_CACHE.write_text(json.dumps(cache, indent=0))
    return cache[key] / k_eff(dataclasses.replace(b, k_scale=1.0), T0, T0)[0]


def solve(b: Body, transport: bool = False) -> Result:
    """Self-regulated equilibrium. transport=True anchors k_eff to OpenMC at the cold state
    (the one-group model then supplies only the temperature dependence)."""
    import dataclasses
    T0 = max(b.T_c, T_SOLIDUS)
    if transport:
        b = dataclasses.replace(b, k_scale=anchor(b, T0))
    k0, g0, d0, _ = k_eff(b, T0, T0)
    res = Result(body=asdict(b), status="", k_cold=k0)
    aD, aE = coefficients(b, T0)
    res.alpha_doppler_pcm_K, res.alpha_expansion_pcm_K, res.alpha_total_pcm_K = aD, aE, aD + aE
    res.dims_cm = dict(d0)
    # total feedback available between the cold state and the temperature limit
    res.feedback_to_limit_pcm = 1e5 * (1 / k_eff(b, b.T_limit, b.T_limit)[0] - 1 / k0) * -1
    m_kg = rho_gcc(T0) * d0["V_cm3"] / 1e3
    res.mass_t = m_kg / 1e3
    res.pu_fissile_kg = g0.fissile_kg_m3 * d0["V_cm3"] * 1e-6
    res.beta_eff, res.gen_time_s = g0.beta_eff, g0.gen_time
    if k0 <= 1.0:
        res.status = "subcritical"
        res.note = f"k_eff {k0:.4f} even when cold (T = {T0:.0f} K): no fission power; increase size, assay or reflector"
        res.dims_cm = {k: v for k, v in d0.items()}
        aD, aE = coefficients(b, T0)
        res.alpha_doppler_pcm_K, res.alpha_expansion_pcm_K, res.alpha_total_pcm_K = aD, aE, aD + aE
        return res
    # adiabatic: temperature where k = 1 (uniform), zero steady power
    if b.removal == "adiabatic":
        lo, hi = T0, b.T_limit
        if k_eff(b, hi, hi)[0] > 1:
            res.status = "runaway"
            res.excess_at_limit_pcm = 1e5 * (1 - 1 / k_eff(b, hi, hi)[0])
            res.note = "still supercritical at the temperature limit: boils / disassembles"
            return res
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if k_eff(b, mid, mid)[0] > 1 else (lo, mid)
        T = 0.5 * (lo + hi)
        res.status = "equilibrium (no heat removal: zero power at the critical temperature)"
        res.T_crit_K = res.T_mean_K = res.T_max_K = res.T_surface_K = T
        res.dims_cm = dims(b, T)
        aD, aE = coefficients(b, T)
        res.alpha_doppler_pcm_K, res.alpha_expansion_pcm_K, res.alpha_total_pcm_K = aD, aE, aD + aE
        return res

    def state(P):
        # self-consistent dims (mean temperature sets expansion)
        Tm = T0
        for _ in range(6):
            kk, g, d, delta = k_eff(b, Tm, Tm)
            pr = profile(b, d, delta, P)
            Tm = pr["T_mean"]
        k, g, d, delta = k_eff(b, pr["T_pw"], pr["T_mean"])
        return k, pr, d, g

    # bracket P: k decreases with P; upper end where T_max hits the limit
    lo, hi = 1.0, 1e6
    while state(hi)[1]["T_max"] < b.T_limit and hi < 1e13:
        hi *= 4
    # find P_limit (T_max = T_limit)
    a, c = lo, hi
    for _ in range(60):
        m = math.sqrt(a * c)
        a, c = (m, c) if state(m)[1]["T_max"] < b.T_limit else (a, m)
    P_lim = a
    k_lim = state(P_lim)[0]
    if k_lim > 1:
        res.status = "runaway"
        res.excess_at_limit_pcm = 1e5 * (1 - 1 / k_lim)
        res.note = (f"still supercritical ({res.excess_at_limit_pcm:.0f} pcm) when the hottest point reaches "
                    f"{b.T_limit:.0f} K at {P_lim/1e6:.3g} MW: no equilibrium below the limit")
        res.P_MW = P_lim / 1e6
        return res
    a, c = lo, P_lim
    if state(a)[0] < 1:
        res.status = "critical only below the coolant temperature"
        res.note = "the coolant/sink is hotter than the critical temperature: the body sits subcritical at P ~ 0"
        return res
    for _ in range(80):
        m = math.sqrt(a * c)
        a, c = (m, c) if state(m)[0] > 1 else (a, m)
    Pst = math.sqrt(a * c)
    k, pr, d, g = state(Pst)
    res.status = "equilibrium"
    res.P_MW = Pst / 1e6
    res.power_density_MW_m3 = Pst / (d["V_cm3"] * 1e-6) / 1e6
    res.T_crit_K, res.T_mean_K, res.T_max_K, res.T_surface_K = pr["T_pw"], pr["T_mean"], pr["T_max"], pr["T_s"]
    res.q2_surface_MW_m2 = pr["q2_MW_m2"]
    res.dims_cm = {k_: v for k_, v in d.items()}
    aD, aE = coefficients(b, pr["T_mean"])
    res.alpha_doppler_pcm_K, res.alpha_expansion_pcm_K, res.alpha_total_pcm_K = aD, aE, aD + aE
    res.flux_n_cm2_s = (Pst / (d["V_cm3"])) / (g.J_per_fission_rate * g.sig_f)
    if pr["T_s"] < T_SOLIDUS:
        res.note = f"surface at {pr['T_s']:.0f} K is below the solidus (~{T_SOLIDUS:.0f} K): a frozen crust would form"
    return res


# --------------------------------------------------------------------------- transient
def transient(b: Body, t_end: float = 600.0, T_start: float | None = None, transport: bool = False):
    """Point kinetics + one lumped temperature, starting cold and just molten.

    The body is assembled at t = 0 at T_start (default the solidus): its cold excess reactivity
    is inserted as a step. Feedback uses the quasi-static profile (the power-weighted temperature
    is the lumped temperature; the surface sits below it by the steady conduction drop).
    Expansion feedback is taken as instantaneous (no inertia): optimistic for fast excursions.
    """
    from scipy.integrate import solve_ivp
    import dataclasses
    T0 = T_start or max(T_SOLIDUS, min(b.T_c, b.T_limit))
    if transport:
        b = dataclasses.replace(b, k_scale=anchor(b, T0))
    k0, g, d0, _ = k_eff(b, T0, T0)
    beta, lam = np.array(g.beta), np.array(g.lam)
    B, Lam = beta.sum(), g.gen_time
    C_th = rho_gcc(T0) * 1e3 * d0["V_cm3"] * 1e-6 * CP_LIQ   # J/K
    n0 = 1e-6                                                # initial power, W (a source-level start)
    Pref = 1e6                                               # W: n is power / Pref

    # precomputed tables keep the stiff integration fast: reactivity vs temperature, the internal
    # conduction drop per watt (linear, constant k), and the cooled area
    Tg = np.linspace(min(T0, 600.0), b.T_limit + 500.0, 120)
    rho_g = np.array([1 - 1 / k_eff(b, T, T)[0] for T in Tg])
    delta = extrap(b, g)
    pr1 = profile(b, d0, delta, 1e6) if b.removal in ("convective", "radiative") else None
    drop_per_W = ((pr1["T_pw"] - pr1["T_s"]) / 1e6) if pr1 and pr1["T_s"] is not None else 0.0
    A = d0["A_cool_cm2"] * 1e-4

    def Q_removed(T, P):
        if b.removal == "adiabatic":
            return 0.0
        if b.removal == "immersed":
            return b.UA * (T - b.T_c)
        Ts = T - drop_per_W * max(P, 0.0)
        if b.removal == "convective":
            return b.h * A * (Ts - b.T_c)
        return SIGMA * b.eps * A * (max(Ts, 1.0) ** 4 - b.T_c**4)

    def rho_of(T):
        return float(np.interp(T, Tg, rho_g))

    def f(t, y):
        n, C, T = y[0], y[1:7], y[7]
        r = rho_of(T)
        dn = (r - B) / Lam * n + (lam * C).sum()
        dC = beta / Lam * n - lam * C
        P = n * Pref
        dT = (P - Q_removed(T, P)) / C_th
        return np.concatenate([[dn], dC, [dT]])

    n_init = n0 / Pref
    y0 = np.concatenate([[n_init], beta / (Lam * lam) * n_init, [T0]])
    sol = solve_ivp(f, (0, t_end), y0, method="Radau", rtol=1e-6, atol=1e-14, dense_output=True)
    t = np.unique(np.concatenate([np.logspace(-6, math.log10(t_end), 400), np.linspace(0, t_end, 200)]))
    Y = sol.sol(t)
    return {"t": t.tolist(), "P_MW": (Y[0] * Pref / 1e6).tolist(), "T_K": Y[7].tolist(),
            "rho0_pcm": 1e5 * rho_of(T0), "beta_pcm": 1e5 * B, "Lambda_s": Lam, "success": bool(sol.success),
            "peak_P_MW": float((Y[0] * Pref).max() / 1e6), "final_P_MW": float(Y[0, -1] * Pref / 1e6),
            "final_T_K": float(Y[7, -1]), "peak_T_K": float(Y[7].max())}


# --------------------------------------------------------------------------- transport check
def openmc_keff(b: Body, T: float, particles=10000, batches=60, inactive=20) -> dict:
    """k_eff of the same body by OpenMC (homogeneous liquid at uniform T; reflector at T_c)."""
    import os, tempfile
    import openmc
    xs = Path(__file__).resolve().parents[2] / "data" / "openmc" / "cross_sections.xml"
    d = dims(b, T)
    fuel = N.fuel_material("UPu_liquid", b.pu, rho_gcc(T))
    fuel.temperature = min(max(T, 1200.0), 2100.0)
    mats = [fuel]
    t_r = 0.0
    if b.reflector:
        mat, rr, t_r = b.reflector
        refl = N.element_material(mat, rr)
        refl.temperature = min(max(b.T_c, 1200.0), 2100.0)
        mats.append(refl)
    if b.shape == "slab":
        h, w = d["t"] / 2, d["W"] / 2
        inner = openmc.model.RectangularParallelepiped(-w, w, -w, w, -h, h)
        outer = openmc.model.RectangularParallelepiped(-w - t_r, w + t_r, -w - t_r, w + t_r, -h - t_r, h + t_r,
                                                        boundary_type="vacuum")
    elif b.shape == "sphere":
        inner = openmc.Sphere(r=d["R"])
        outer = openmc.Sphere(r=d["R"] + t_r, boundary_type="vacuum")
    else:
        inner = openmc.model.RightCircularCylinder((0, 0, -d["H"] / 2), d["H"], d["R"])
        outer = openmc.model.RightCircularCylinder((0, 0, -d["H"] / 2 - t_r), d["H"] + 2 * t_r, d["R"] + t_r,
                                                   boundary_type="vacuum")
    cells = [openmc.Cell(fill=fuel, region=-inner)]
    if b.reflector:
        cells.append(openmc.Cell(fill=mats[1], region=+inner & -outer))
    geom = openmc.Geometry(cells)
    if not b.reflector:  # vacuum on the fuel surface itself
        for srf in geom.get_all_surfaces().values():
            srf.boundary_type = "vacuum"
    st = openmc.Settings()
    st.particles, st.batches, st.inactive = particles, batches, inactive
    ext = d.get("t", d.get("R", 10)) / 4
    st.source = openmc.IndependentSource(space=openmc.stats.Box((-ext, -ext, -ext), (ext, ext, ext)))
    st.temperature = {"method": "interpolation", "default": fuel.temperature}
    st.output = {"tallies": False, "summary": False}
    model = openmc.Model(geom, openmc.Materials(mats), st)
    model.materials.cross_sections = str(xs)
    with tempfile.TemporaryDirectory() as tmp:
        cwd = os.getcwd(); os.chdir(tmp)
        try:
            sp = model.run(threads=int(os.environ.get("OMP_THREADS", "4")), output=False)
            with openmc.StatePoint(sp) as f:
                k = f.keff
        finally:
            os.chdir(cwd)
    k_model = k_eff(b, T, T)[0]
    return {"T_K": T, "openmc_k": float(k.nominal_value), "openmc_sd": float(k.std_dev), "model_k": k_model,
            "dk_pcm": 1e5 * (k_model - float(k.nominal_value)), "dims_cm": d}


CAL_CASES = [  # (shape, size cm, pu, width/height) bare bodies spanning the sizes of interest
    ("slab", 15, 0.20, 300), ("slab", 25, 0.15, 300), ("slab", 40, 0.12, 300), ("slab", 60, 0.10, 300),
    ("slab", 25, 0.10, 300), ("slab", 25, 0.20, 300),
    ("sphere", 8, 0.20, 0), ("sphere", 12, 0.15, 0), ("sphere", 20, 0.10, 0),
    ("cylinder", 12, 0.15, 24), ("cylinder", 25, 0.10, 50),
]


def calibrate(T=1500.0):
    """Fit the leakage factor f and extrapolation coefficient c to OpenMC k_eff of bare bodies."""
    import dataclasses
    rows = []
    for shape, size, pu, extra in CAL_CASES:
        b = Body(shape=shape, size_cm=size, pu=pu, width_cm=extra if shape == "slab" else 0.0,
                 height_cm=extra if shape == "cylinder" else 0.0, T_c=T)
        c = openmc_keff(b, T)
        g = one_group(b, T, T)
        rows.append({"shape": shape, "size_cm": size, "pu": pu, "openmc_k": c["openmc_k"], "openmc_sd": c["openmc_sd"],
                     "k_inf": g.k_inf, "D": g.D, "M2": g.M2, "dims": c["dims_cm"]})
        print(rows[-1]["shape"], size, pu, f"OpenMC {c['openmc_k']:.4f}", flush=True)

    def k_of(r, f, cc):
        b = Body(shape=r["shape"], size_cm=r["size_cm"], pu=r["pu"])
        d = r["dims"]
        bb = dataclasses.replace(b, width_cm=d.get("W", 0.0))
        B2 = buckling(bb, d, cc * r["D"])
        return r["k_inf"] / (1 + f * r["M2"] * B2)
    best = None
    for f in np.linspace(0.5, 1.3, 81):
        for cc in np.linspace(0.0, 6.0, 121):
            err = sum((k_of(r, f, cc) - r["openmc_k"]) ** 2 for r in rows)
            if best is None or err < best[0]:
                best = (err, f, cc)
    _, f, cc = best
    for r in rows:
        r["model_raw_k"] = k_of(r, 1.0, 2.13)
        r["model_cal_k"] = k_of(r, f, cc)
        r["residual_pcm"] = 1e5 * (r["model_cal_k"] - r["openmc_k"])
    out = {"constants": str(N.CONSTANTS), "f": float(f), "c": float(cc), "T_K": T,
           "rms_residual_pcm": float(np.sqrt(np.mean([r["residual_pcm"] ** 2 for r in rows]))),
           "max_residual_pcm": float(max(abs(r["residual_pcm"]) for r in rows)), "cases": rows}
    CALIBRATION.write_text(json.dumps(out, indent=1))
    print(f"f = {f:.3f}, c = {cc:.2f}; residual rms {out['rms_residual_pcm']:.0f} pcm, max {out['max_residual_pcm']:.0f} pcm")
    return out


def window(b: Body, transport: bool = True, n_points: int = 5) -> dict:
    """The self-regulating window in size: from first criticality (cold) to the size above which
    the body is still supercritical when its hottest point reaches T_limit. Power along the window.

    The OpenMC anchor (k_scale) varies slowly with size, so it is computed at the window edges
    and interpolated in between (two refinement passes).
    """
    import dataclasses
    T0 = max(b.T_c, T_SOLIDUS)

    def scaled(size, scale):
        return dataclasses.replace(b, size_cm=size, k_scale=scale)

    def find(pred, lo, hi):
        for _ in range(50):
            mid = 0.5 * (lo + hi)
            lo, hi = (lo, mid) if pred(mid) else (mid, hi)
        return 0.5 * (lo + hi)

    # one OpenMC anchor at the critical size: the window is < 1 % in size, and two independent anchors
    # would add their statistical noise (~ the whole feedback budget) to the window edges
    crit = lambda s_, sc: k_eff(scaled(s_, sc), T0, T0)[0] >= 1.0
    scale = 1.0
    lo_size = find(lambda s_: crit(s_, scale), 0.5, 500.0)
    if transport:
        for _ in range(2):
            scale = anchor(scaled(round(lo_size, 3), 1.0), T0)
            lo_size = find(lambda s_: crit(s_, scale), 0.5, 500.0)
    runaway = lambda s_: solve(scaled(s_, scale)).status == "runaway"
    hi_size = find(runaway, lo_size, lo_size * 1.5 + 5)
    scale_lo = scale_hi = scale
    pts = []
    for i in range(n_points):
        f = (i + 0.5) / n_points
        s_ = lo_size + f * (hi_size - lo_size)
        sc = scale_lo + f * (scale_hi - scale_lo)
        r = solve(scaled(s_, sc))
        pts.append({"size_cm": s_, "P_MW": r.P_MW, "T_max_K": r.T_max_K, "T_surface_K": r.T_surface_K,
                    "q2_MW_m2": r.q2_surface_MW_m2, "k_cold": r.k_cold, "status": r.status})
    r_hi = solve(scaled(hi_size * 0.9999, scale_hi))
    return {"body": asdict(b), "transport": transport, "critical_size_cm": lo_size, "runaway_size_cm": hi_size,
            "window_cm": hi_size - lo_size, "window_pct": 100 * (hi_size / lo_size - 1),
            "max_power_MW": r_hi.P_MW, "max_power_T_max_K": r_hi.T_max_K, "anchors": [scale_lo, scale_hi],
            "feedback_to_limit_pcm": r_hi.feedback_to_limit_pcm, "mass_t_at_critical": solve(scaled(lo_size, scale_lo)).mass_t,
            "points": pts}


# --------------------------------------------------------------------------- CLI
def body_from(a) -> Body:
    refl = None
    if a.reflector:
        mat, thick = a.reflector.split(":")
        rho = {"W": 19.0, "Mo": 10.0, "steel": 7.6, "Pb": 10.0, "U": 18.9, "Be": 1.85, "C": 1.8}[mat]
        refl = (mat, rho, float(thick))
    return Body(shape=a.shape, size_cm=a.size[0], height_cm=a.height, width_cm=a.width, pu=a.pu[0],
                reflector=refl, removal=a.removal, h=a.h, eps=a.eps, UA=a.UA, T_c=a.Tc, faces=a.faces,
                nu=a.nu, T_limit=a.T_limit)


def show(r: Result) -> str:
    C = 273.15
    b = r.body
    head = (f"{b['shape']} {b['size_cm']:g} cm, Pu {b['pu']:.3f}, removal {b['removal']}"
            + (f", reflector {b['reflector'][0]} {b['reflector'][2]:g} cm" if b["reflector"] else ""))
    lines = [head, f"  status: {r.status}   k_eff cold {r.k_cold:.4f}   mass {r.mass_t:.2f} t, fissile Pu {r.pu_fissile_kg:.0f} kg"]
    if r.status == "equilibrium":
        lines += [
            f"  power {r.P_MW:.4g} MW ({r.power_density_MW_m3:.3g} MW/m3); surface heat flux {r.q2_surface_MW_m2:.3g} MW/m2",
            f"  temperatures: surface {r.T_surface_K - C:.0f} C, mean {r.T_mean_K - C:.0f} C, max {r.T_max_K - C:.0f} C; "
            f"critical (power-weighted) {r.T_crit_K - C:.0f} C",
            f"  flux {r.flux_n_cm2_s:.2e} n/cm2 s"]
    elif r.T_crit_K:
        lines.append(f"  critical temperature {r.T_crit_K - C:.0f} C")
    lines.append(f"  feedback cold -> {b['T_limit']:.0f} K: {r.feedback_to_limit_pcm:.0f} pcm available; cold excess "
                 f"{1e5 * (1 - 1 / r.k_cold):.0f} pcm")
    lines.append(f"  feedback: Doppler {r.alpha_doppler_pcm_K:.2f}, expansion {r.alpha_expansion_pcm_K:.2f}, "
                 f"total {r.alpha_total_pcm_K:.2f} pcm/K; beta_eff {r.beta_eff*1e5:.0f} pcm, Lambda {r.gen_time_s*1e6:.2f} us")
    if r.note:
        lines.append(f"  note: {r.note}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", nargs="?", default="solve", choices=["solve", "scan", "transient", "check", "calibrate", "window"])
    ap.add_argument("--shape", default="slab", choices=["slab", "sphere", "cylinder"])
    ap.add_argument("--size", type=float, nargs="+", default=[30.0], help="cm: slab thickness / radius")
    ap.add_argument("--height", type=float, default=0.0)
    ap.add_argument("--width", type=float, default=0.0)
    ap.add_argument("--pu", type=float, nargs="+", default=[0.15])
    ap.add_argument("--reflector", default=None, help="material:thickness_cm, e.g. W:20")
    ap.add_argument("--removal", default="convective", choices=["adiabatic", "convective", "radiative", "immersed"])
    ap.add_argument("--h", type=float, default=2.0e4)
    ap.add_argument("--eps", type=float, default=0.8)
    ap.add_argument("--UA", type=float, default=1.0e6)
    ap.add_argument("--Tc", type=float, default=1500.0)
    ap.add_argument("--faces", type=int, default=2)
    ap.add_argument("--nu", type=float, default=1.0)
    ap.add_argument("--T-limit", type=float, default=3500.0)
    ap.add_argument("--t-end", type=float, default=600.0)
    ap.add_argument("--json", default=None, help="write results to this file")
    ap.add_argument("--transport", action="store_true", help="anchor k_eff to OpenMC (10-20 s per body)")
    a = ap.parse_args()
    out = []
    if a.cmd == "solve":
        r = solve(body_from(a), transport=a.transport)
        print(show(r))
        out = [asdict(r)]
    elif a.cmd == "scan":
        import dataclasses
        base = body_from(a)
        print("k_eff anchored to OpenMC at the cold state" if a.transport else
              f"fast mode: one-group diffusion, leakage calibration f, c = {_cal()} (see pool_calibration.json)")
        print(f"{'Pu':>6} {"size":>7} {'k_cold':>7} {'status':>12} {'P_MW':>10} {'T_max_C':>8} {'q2_MW/m2':>9}")
        for pu in a.pu:
            for s in a.size:
                r = solve(dataclasses.replace(base, pu=pu, size_cm=s), transport=a.transport)
                st = r.status.split(" ")[0]
                print(f"{pu:6.3f} {s:7.2f} {r.k_cold:7.4f} {st:>12} {r.P_MW:10.4g} "
                      f"{(r.T_max_K - 273.15) if r.T_max_K else float('nan'):8.0f} {r.q2_surface_MW_m2:9.3g}")
                out.append(asdict(r))
    elif a.cmd == "window":
        out = []
        for pu in a.pu:
            w = window(body_from(a).__class__(**{**asdict(body_from(a)), "pu": pu}), transport=a.transport)
            print(f"Pu {pu:.3f}: critical at {w['critical_size_cm']:.2f} cm ({w['mass_t_at_critical']:.1f} t), runaway above "
                  f"{w['runaway_size_cm']:.2f} cm: window {w['window_cm']:.2f} cm ({w['window_pct']:.2f} %); "
                  f"max self-regulated power {w['max_power_MW']:.3g} MW (hottest point {w['max_power_T_max_K'] - 273.15:.0f} C)")
            for p_ in w["points"]:
                print(f"    size {p_['size_cm']:.2f} cm: {p_['P_MW']:.3g} MW, surface {p_['T_surface_K'] - 273.15:.0f} C, "
                      f"max {p_['T_max_K'] - 273.15:.0f} C, {p_['q2_MW_m2']:.3g} MW/m2")
            out.append(w)
    elif a.cmd == "calibrate":
        out = [calibrate()]
    elif a.cmd == "check":
        b = body_from(a)
        c = openmc_keff(b, max(b.T_c, T_SOLIDUS))
        print(f"k_eff at {c['T_K']:.0f} K: OpenMC {c['openmc_k']:.4f} +- {c['openmc_sd']:.4f}, one-group model "
              f"{c['model_k']:.4f} (model - OpenMC = {c['dk_pcm']:.0f} pcm)")
        out = [c]
    else:
        tr = transient(body_from(a), a.t_end, transport=a.transport)
        print(f"inserted {tr['rho0_pcm']:.0f} pcm ({tr['rho0_pcm']/tr['beta_pcm']:.2f} $); peak {tr['peak_P_MW']:.4g} MW; "
              f"final {tr['final_P_MW']:.4g} MW at {tr['final_T_K'] - 273.15:.0f} C (peak {tr['peak_T_K'] - 273.15:.0f} C)")
        out = [tr]
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

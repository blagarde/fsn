"""Transient simulator: point kinetics (6 delayed groups) + lumped core thermal-hydraulics + decay heat.

State: n (fission power / nominal), C_1..6 (precursors), H_1..8 (decay-heat groups),
T_f (fuel), T_c (in-core coolant and walls), T_L (loop / hot pool, returns as core inlet).

  dn/dt   = (rho - beta)/Lambda n + sum lam_i C_i
  dC_i/dt = beta_i/Lambda n - lam_i C_i
  dH_j/dt = a_j n - mu_j H_j                       decay heat, Way-Wigner fitted by 8 exponentials
  C_f dT_f/dt = P0 [(1-f_d) n + sum H_j] - (T_f - T_c)/R_fc
  C_c dT_c/dt = (T_f - T_c)/R_fc - m_dot cp (T_out - T_in),   T_out = 2 T_c - T_in
  C_L dT_L/dt = m_dot cp (T_out - T_L) - Q_sink(t, T_L),        T_in = T_L
  rho = rho_ext(t) + K_D ln(T_f/T_f0) + a_f (T_f - T_f0) + a_c (T_c - T_c0)

All parameters come from core.solve() (Steady), so the transient is consistent with the
steady state. Scenarios: reactivity step (UTOP), loss of flow (ULOF), loss of heat sink (ULOHS),
scram, load following. "Unprotected" = no scram; the feedbacks alone set the outcome.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from core import decay_heat_fraction


def decay_groups(T_op=6.3e7, n=8):
    """Exponential fit (amplitudes A_j = a_j/mu_j >= 0) of Way-Wigner decay heat after long operation."""
    mus = np.logspace(-6, 0.5, n)
    t = np.logspace(0, 7.5, 200)
    y = np.array([decay_heat_fraction(x, T_op) for x in t])
    Amat = np.exp(-np.outer(t, mus))
    A, *_ = np.linalg.lstsq(Amat / y[:, None], np.ones_like(t), rcond=None)  # relative-error fit
    A = np.clip(A, 0, None)
    return mus, A


@dataclass
class Scenario:
    name: str
    t_end: float = 600.0
    rho_ext: callable = lambda t: 0.0          # pcm
    flow: callable = lambda t: 1.0             # fraction of nominal
    sink: callable = lambda t: 1.0             # heat-sink capacity fraction of nominal
    loop_heat_capacity_factor: float = 20.0    # loop/pool heat capacity relative to in-core coolant (pool-type
                                               # primary ~10-50; loop-type ~3-5). APPROX, stated in results


def run(st, sc: Scenario, cp_cool: float | None = None):
    P0 = st.P_MW * 1e6
    beta = np.array(st.beta) * st.beta_retained
    lam = np.array(st.lam)
    B = beta.sum()
    Lam = st.gen_time_s
    mus, A = decay_groups()
    f_d = A.sum()
    a = A * mus
    Cf = st.fuel_heat_capacity_MJ_K * 1e6
    Cc = st.coolant_heat_capacity_MJ_K * 1e6
    CL = Cc * sc.loop_heat_capacity_factor
    R = st.R_fuel_to_coolant_K_per_MW / 1e6
    spec = st.spec
    Tin0, Tout0 = spec["T_in"], spec["T_out"]
    Tc0 = 0.5 * (Tin0 + Tout0)
    Tf0 = st.T_fuel_avg_K
    mcp0 = P0 / (Tout0 - Tin0)
    T_sink = Tin0 - 200.0      # sink temperature: the sink removes UA (T_L - T_sink)
    UA0 = P0 / (Tin0 - T_sink)
    KD, af, ac = st.doppler_K_D_pcm, st.fuel_density_pcm_per_K, st.coolant_density_pcm_per_K

    def rho_of(t, Tf, Tc):
        return 1e-5 * (sc.rho_ext(t) + KD * math.log(max(Tf, 1.0) / Tf0) + af * (Tf - Tf0) + ac * (Tc - Tc0))

    def f(t, y):
        n, C, H, Tf, Tc, TL = y[0], y[1:7], y[7:15], y[15], y[16], y[17]
        rho = rho_of(t, Tf, Tc)
        dn = (rho - B) / Lam * n + (lam * C).sum()
        dC = beta / Lam * n - lam * C
        dH = a * n - mus * H
        Pheat = P0 * ((1 - f_d) * n + H.sum())
        Tin = TL
        mcp = mcp0 * max(sc.flow(t), 1e-4)
        # linear-profile closure; at very low flow the outlet cannot run away from the fuel
        Tout = min(2 * Tc - Tin, max(Tf, Tout0 + (Tf - Tf0)))
        q_fc = (Tf - Tc) / R
        dTf = (Pheat - q_fc) / Cf
        dTc = (q_fc - mcp * (Tout - Tin)) / Cc
        dTL = (mcp * (Tout - TL) - sc.sink(t) * UA0 * (TL - T_sink)) / CL
        return np.concatenate([[dn], dC, dH, [dTf, dTc, dTL]])

    y0 = np.concatenate([[1.0], beta / (Lam * lam), A, [Tf0, Tc0, Tin0]])
    sol = solve_ivp(f, (0, sc.t_end), y0, method="Radau", rtol=1e-6, atol=1e-9, dense_output=True, max_step=sc.t_end / 200)
    t = np.unique(np.concatenate([np.logspace(-4, math.log10(sc.t_end), 300), np.linspace(0, sc.t_end, 300)]))
    Y = sol.sol(t)
    n, H, Tf, Tc, TL = Y[0], Y[7:15], Y[15], Y[16], Y[17]
    Pheat = (1 - f_d) * n + H.sum(axis=0)
    rho = np.array([rho_of(ti, a_, b_) for ti, a_, b_ in zip(t, Tf, Tc)]) * 1e5
    Tout = np.minimum(2 * Tc - TL, np.maximum(Tf, Tout0 + (Tf - Tf0)))
    def first(mask):
        idx = np.argmax(mask)
        return float(t[idx]) if mask.any() else None
    t_fuel = first(Tf > st.T_fuel_limit_K)
    t_boil = first(Tout > st.T_coolant_boil_K) if st.T_coolant_boil_K else None
    return {"scenario": sc.name, "loop_heat_capacity_factor": sc.loop_heat_capacity_factor,
            "t_fuel_limit_s": t_fuel, "t_coolant_boil_s": t_boil,
            "valid_until_s": min(x for x in (t_fuel, t_boil, sc.t_end) if x is not None), "t": t.tolist(), "power_frac": Pheat.tolist(), "fission_frac": n.tolist(),
            "T_fuel_K": Tf.tolist(), "T_coolant_K": Tc.tolist(), "T_in_K": TL.tolist(), "T_out_K": Tout.tolist(),
            "rho_pcm": rho.tolist(), "beta_pcm": B * 1e5, "success": bool(sol.success),
            "peak": {"T_fuel_K": float(Tf.max()), "T_out_K": float(Tout.max()), "power_frac": float(Pheat.max())},
            "final": {"T_fuel_K": float(Tf[-1]), "T_out_K": float(Tout[-1]), "power_frac": float(Pheat[-1])}}


def standard_scenarios(st) -> list[Scenario]:
    beta_pcm = sum(st.beta) * st.beta_retained * 1e5
    return [
        Scenario("UTOP: +0.5 $ step, no scram", 300, rho_ext=lambda t: 0.5 * beta_pcm if t > 1 else 0.0),
        Scenario("ULOF: pump coastdown (20 s halving) to 5 % natural circulation, no scram", 600,
                 flow=lambda t: max(0.05, 1 / (1 + t / 20.0)) if t > 1 else 1.0),
        Scenario("ULOHS: heat sink lost, flow kept, no scram", 1800, sink=lambda t: 0.0 if t > 1 else 1.0),
        Scenario("Load follow: heat demand to 50 %, no rod motion", 1800, sink=lambda t: 0.5 if t > 1 else 1.0),
        Scenario("Scram (-10 $) with flow kept", 600, rho_ext=lambda t: -10 * beta_pcm if t > 1 else 0.0),
        Scenario("Scram + total loss of flow and sink", 3600, rho_ext=lambda t: -10 * beta_pcm if t > 1 else 0.0,
                 flow=lambda t: 1e-3 if t > 1 else 1.0, sink=lambda t: 0.0 if t > 1 else 1.0),
    ]

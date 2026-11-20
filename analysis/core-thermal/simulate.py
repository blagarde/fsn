"""Core nuclear-thermal simulator: command-line entry point.

  python simulate.py steady CASE [--pu 0.15 --f-fuel 0.4 --power MW ...]   one core, full report
  python simulate.py curve CASE                  fuel/wall peak temperature vs power density
  python simulate.py sweep [CASE ...]            fissile density sweep -> results/sweep.json
  python simulate.py transient CASE              standard scenarios -> results/transients_CASE.json
  python simulate.py all                         everything the study page uses

Run with the nuc environment: /opt/mamba/envs/nuc/bin/python (OpenMC, SciPy).
Cases live in cases.py; any CoreSpec field can be overridden with --set field=value.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import math
from pathlib import Path

import cases as CS
import core
import kinetics as K
import thermal as TH

OUT = Path(__file__).resolve().parent / "results"


def spec_for(name, overrides=()):
    s = dataclasses.replace(CS.CASES[name])
    for kv in overrides:
        k, v = kv.split("=", 1)
        cur = getattr(s, k)
        val = None if v == "None" else (type(cur)(v) if cur is not None and not isinstance(cur, tuple) else json.loads(v))
        s = dataclasses.replace(s, **{k: val})
    return s


def fmt(st) -> str:
    if not st.critical:
        return f"k_inf {st.k_inf:.3f} <= 1: not critical at any size"
    C = 273.15
    lines = [
        f"k_inf {st.k_inf:.3f}  CR(core) {st.cr_core:.2f}  spectrum weights {st.moderating_weights} {st.note}",
        f"critical core R {st.R_m:.2f} m, H {st.H_m:.2f} m, V {st.V_m3:.2f} m3; fissile {st.fissile_kg_m3:.0f} kg/m3 -> {st.fissile_kg/1e3:.2f} t fissile, {st.hm_kg/1e3:.1f} t HM",
        f"volume fractions {', '.join(f'{k} {v:.3f}' for k, v in st.fractions.items())}; radial peaking {st.F_radial:.2f}",
        f"power limit: {st.limit}: q''' {st.q3_max_MW_m3:.0f} MW/m3 core avg -> P {st.P_MW:.0f} MWth, {st.specific_power_kW_kg_fissile:.0f} kW/kg fissile",
        f"flux {st.flux_avg_n_cm2_s:.2e} n/cm2 s (avg); fluence {st.fast_fluence_per_fpy:.1e} n/cm2 per full-power year",
        f"peak fuel {st.T_fuel_max_K - C:.0f} C, peak wall {st.T_wall_max_K - C:.0f} C, wall heat flux {st.q2_wall_max_MW_m2:.2f} MW/m2; mean fuel {st.T_fuel_avg_K - C:.0f} C",
        f"coolant {st.m_dot_kg_s:.0f} kg/s = {st.vol_flow_m3_s:.2f} m3/s, v {st.velocity_m_s:.1f} m/s, core dp {st.dp_core_bar:.2f} bar, core pumping {st.pumping_core_MW:.2f} MW ({100*st.pumping_core_MW/max(st.P_MW,1e-9):.2f} %)",
        f"beta_eff {st.beta_eff*1e5:.0f} pcm (retained {st.beta_retained:.2f}), Lambda {st.gen_time_s*1e6:.2f} us",
        f"Doppler T dk/dT {st.doppler_K_D_pcm:.0f} pcm; fuel density {st.fuel_density_pcm_per_K:.2f} pcm/K; coolant density {st.coolant_density_pcm_per_K:.2f} pcm/K; full coolant void {st.coolant_void_pcm:.0f} pcm",
        f"core heat capacity {st.heat_capacity_core_MJ_K:.1f} MJ/K -> adiabatic {st.adiabatic_rate_K_s:.1f} K/s at full power; decay heat " + ", ".join(f"{k} {v:.1f} MW" for k, v in st.decay_MW.items()),
        f"no cooling after scram: fuel limit reached after {st.adiabatic_after_scram_s_to_limit/3600:.1f} h (adiabatic core, Way-Wigner decay heat)",
    ]
    return "\n".join(lines)


def curve(spec, n=12):
    st = core.solve(spec)
    if not st.critical:
        return []
    fr = core.fractions(spec)
    cell = core.make_cell(spec)
    cool = core._fluid(spec)
    out = []
    for q in [st.q3_max_MW_m3 * x for x in (0.1, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5)]:
        r = TH.hot_channel(cell, cool, q * 1e6, fr["f_fuel"], fr["f_cool"], st.H_m, spec.T_in, spec.T_out,
                           st.F_radial, extrap=0.1, orificed=spec.orificed)
        out.append({"q3_MW_m3": q, "P_MW": q * st.V_m3, "T_fuel_max_K": r.T_fuel_max, "T_wall_max_K": r.T_wall_max,
                    "m_dot_kg_s": q * 1e6 * st.V_m3 / (cool.cp(0.5 * (spec.T_in + spec.T_out)) * (spec.T_out - spec.T_in)),
                    "v_m_s": r.v})
    return out


def sweep(names):
    res = {}
    for name in names:
        rows = []
        for pu in CS.PU_GRID:
            for ff in CS.FFUEL_GRID:
                s = dataclasses.replace(CS.CASES[name], pu=pu, f_fuel=ff)
                try:
                    st = core.solve(s)
                except ValueError as e:
                    rows.append({"pu": pu, "f_fuel": ff, "error": str(e)})
                    continue
                d = dataclasses.asdict(st)
                d.pop("spec")
                d.update(pu=pu, f_fuel=ff)
                rows.append(d)
                print(f"{name} pu {pu:.2f} f_fuel {ff:.2f}: k_inf {st.k_inf:.3f}" +
                      (f" V {st.V_m3:.1f} m3 P {st.P_MW:.0f} MW limit {st.limit}" if st.critical else ""), flush=True)
        res[name] = rows
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["steady", "curve", "sweep", "transient", "all"])
    ap.add_argument("cases", nargs="*")
    ap.add_argument("--set", nargs="*", default=[], help="CoreSpec overrides field=value")
    ap.add_argument("--power", type=float, default=None, help="MWth (steady): temperatures at this power")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    names = a.cases or list(CS.CASES)
    if a.cmd == "steady":
        for n in names:
            print(f"== {n}: {CS.CASES[n].name}")
            print(fmt(core.solve(spec_for(n, a.set), a.power)))
    elif a.cmd == "curve":
        for n in names:
            print(json.dumps(curve(spec_for(n, a.set)), indent=1))
    elif a.cmd in ("sweep", "all"):
        steady = {}
        for n in names:
            st = core.solve(spec_for(n, a.set))
            print(f"== {n}\n{fmt(st)}", flush=True)
            steady[n] = dataclasses.asdict(st)
            steady[n]["curve"] = curve(spec_for(n, a.set)) if not CS.CASES[n].circulating else []
        (OUT / "reference.json").write_text(json.dumps(steady, indent=1, default=str))
        (OUT / "sweep.json").write_text(json.dumps(sweep(names), indent=1, default=str))
        if a.cmd == "all":
            a.cmd = "transient"
    if a.cmd == "transient":
        out = {}
        for n in names:
            st = core.solve(spec_for(n, a.set))
            if not st.critical or CS.CASES[n].circulating:
                continue
            out[n] = []
            for sc in K.standard_scenarios(st):
                r = K.run(st, sc)
                print(f"{n} | {sc.name}: peak fuel {r['peak']['T_fuel_K']-273.15:.0f} C, peak outlet {r['peak']['T_out_K']-273.15:.0f} C, "
                      f"peak power {r['peak']['power_frac']:.2f}; final power {r['final']['power_frac']:.3f}, fuel {r['final']['T_fuel_K']-273.15:.0f} C", flush=True)
                out[n].append(r)
        (OUT / "transients.json").write_text(json.dumps(out))


if __name__ == "__main__":
    main()

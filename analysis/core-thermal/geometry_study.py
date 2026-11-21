"""Liquid-fuel geometry and reflector options with pool.py (refines docs/studies/geometry-by-phase.md).

A pool of molten U-Pu (Pu 15 %) in a cylinder of fixed radius: heating makes the liquid rise
(free surface), so expansion acts along the axis. Natural convection keeps the liquid well mixed
(nu = 0); walls cooled by a liquid metal at 1,500 K, h = 20 kW/m2 K. For each case: cold critical
size and mass, feedback available up to boiling, self-regulating window and power, and for
reflected cases the OpenMC worth of the reflector (the most a movable reflector could control).

Writes results/geometry_study.json. Run: /opt/mamba/envs/nuc/bin/python geometry_study.py
"""
import dataclasses
import json
from pathlib import Path

import pool

OUT = Path(__file__).resolve().parent / "results" / "geometry_study.json"
BASE = pool.Body(shape="cylinder", pu=0.15, removal="convective", h=2e4, T_c=1500, nu=0.0, faces=2)

CASES = {f"bare_HD{hd:g}": dataclasses.replace(BASE, h_over_d=hd) for hd in (0.25, 0.5, 1, 2, 4)}
for name, refl in {"W20": ("W", 19.0, 20.0), "Pb30": ("Pb", 9.8, 30.0), "steel30": ("steel", 7.6, 30.0),
                   "BeO20": ("BeO", 3.0, 20.0), "Udep40": ("Udep", 18.9, 40.0), "graphite30": ("graphite", 1.8, 30.0)}.items():
    CASES[f"HD1_{name}"] = dataclasses.replace(BASE, reflector=refl)
CASES["HD1_W20_radial"] = dataclasses.replace(BASE, reflector=("W", 19.0, 20.0), refl_faces="radial")
CASES["HD1_W20_axial"] = dataclasses.replace(BASE, reflector=("W", 19.0, 20.0), refl_faces="axial")
CASES["HD0.25_W20_radial"] = dataclasses.replace(BASE, h_over_d=0.25, reflector=("W", 19.0, 20.0), refl_faces="radial")
CASES["HD4_W20_radial"] = dataclasses.replace(BASE, h_over_d=4, reflector=("W", 19.0, 20.0), refl_faces="radial")


def main():
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    for name, b in CASES.items():
        if name in res:
            continue
        w = pool.window(b, transport=True, n_points=3)
        crit = dataclasses.replace(b, size_cm=w["critical_size_cm"], k_scale=w["anchors"][0], delta_fit=w["delta_fit_cm"])
        aD, aE = pool.coefficients(crit, 1500.0)
        w["alpha_doppler_pcm_K"], w["alpha_expansion_pcm_K"] = aD, aE
        w["dims_at_critical"] = pool.dims(crit, 1500.0)
        if b.reflector:
            w["reflector_worth"] = pool.reflector_worth(dataclasses.replace(b, size_cm=w["critical_size_cm"]))
        res[name] = w
        print(f"{name}: R {w['critical_size_cm']:.2f} cm, {w['mass_t_at_critical']:.2f} t, feedback {w['feedback_to_limit_pcm']:.0f} pcm, "
              f"window {w['window_pct']:.2f} %, P {w['max_power_MW']:.3g} MW"
              + (f", reflector worth {w['reflector_worth']['worth_pcm']:.0f} pcm" if b.reflector else ""), flush=True)
        OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

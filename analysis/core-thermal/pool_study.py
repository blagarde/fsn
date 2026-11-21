"""Configurations for the study page: self-regulating windows of simple molten U-Pu bodies.

Writes results/pool_study.json. Run: /opt/mamba/envs/nuc/bin/python pool_study.py  (~30-60 min, OpenMC)
"""
import dataclasses
import json
from pathlib import Path

import pool

OUT = Path(__file__).resolve().parent / "results" / "pool_study.json"
SLAB = pool.Body(shape="slab", width_cm=300, pu=0.15, removal="convective", h=2e4, T_c=1500, faces=2, nu=1.0)

CASES = {
    # assay
    "slab_pu10": dataclasses.replace(SLAB, pu=0.10),
    "slab_pu15": SLAB,
    "slab_pu20": dataclasses.replace(SLAB, pu=0.20),
    # heat removal and internal mixing (Pu 0.15)
    "slab_mixed": dataclasses.replace(SLAB, nu=0.0),
    "slab_nu10": dataclasses.replace(SLAB, nu=10.0),
    "slab_one_face": dataclasses.replace(SLAB, faces=1),
    "slab_radiative_1500": dataclasses.replace(SLAB, removal="radiative", eps=0.8, T_c=1500),
    "slab_radiative_1000": dataclasses.replace(SLAB, removal="radiative", eps=0.8, T_c=1000),
    "slab_adiabatic": dataclasses.replace(SLAB, removal="adiabatic"),
    # shape and reflector
    "sphere_bare": pool.Body(shape="sphere", pu=0.15, removal="convective", h=2e4, T_c=1500, nu=1.0),
    "sphere_W20": pool.Body(shape="sphere", pu=0.15, removal="convective", h=2e4, T_c=1500, nu=1.0, reflector=("W", 19.0, 20.0)),
    "cylinder_HD1": pool.Body(shape="cylinder", pu=0.15, removal="convective", h=2e4, T_c=1500, nu=1.0, faces=2),
}


def main():
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    for name, b in CASES.items():
        if name in res:
            continue
        if b.removal == "adiabatic":
            w = pool.window(dataclasses.replace(b, removal="convective"), transport=True)
            r = pool.solve(dataclasses.replace(b, size_cm=0.5 * (w["critical_size_cm"] + w["runaway_size_cm"]),
                                               k_scale=w["anchors"][0]))
            res[name] = {"window_from": "convective twin", "mid_window": dataclasses.asdict(r)}
        else:
            res[name] = pool.window(b, transport=True)
            w = res[name]
            print(name, f"{w['critical_size_cm']:.2f}-{w['runaway_size_cm']:.2f} cm, max {w['max_power_MW']:.3g} MW", flush=True)
        OUT.write_text(json.dumps(res, indent=1))
    # assembly transient at the middle of the Pu 0.15 slab window
    w = res["slab_pu15"]
    mid = 0.5 * (w["critical_size_cm"] + w["runaway_size_cm"])
    steady = pool.solve(dataclasses.replace(SLAB, size_cm=mid, k_scale=w["anchors"][0]))
    tr = pool.transient(dataclasses.replace(SLAB, size_cm=mid, k_scale=w["anchors"][0]), t_end=3000)
    tr["steady_P_MW"], tr["steady_T_crit_K"], tr["size_cm"] = steady.P_MW, steady.T_crit_K, mid
    res["transient_slab_mid"] = {k: v for k, v in tr.items()}
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

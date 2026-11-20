"""Run the Phase-1 infinite-medium screen for one or more B-family cases.

Usage: python run_neutronics.py B1 [B2 ...]   (writes results/neutronics_<case>.json)
Steps per case: k_inf at three Pu fractions -> quadratic fit -> Pu fraction for k_inf = 1.15 ->
full run there (CR, spectrum, absorbers) -> coolant void worth -> 1200 vs 2100 K -> isotope variants.
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np

from bfam import HERE, screen_plus, worth_pcm, void
from designs import DESIGNS

K_TARGET = 1.15
SCAN = {"B4": [0.10, 0.18, 0.26], "B4-natCl": [0.20, 0.30, 0.40], "B3-C": [0.14, 0.20, 0.26], "B3-N": [0.14, 0.20, 0.26]}
DEFAULT_SCAN = [0.12, 0.18, 0.24]
STAT = dict(particles=20000, batches=60, inactive=20, threads=1)
SCAN_STAT = dict(particles=10000, batches=40, inactive=15, threads=1)  # scan points only feed the fit


def solve_x(xs, ks):
    c = np.polyfit(xs, ks, 2 if len(xs) >= 3 else 1)
    roots = [r.real for r in np.roots(np.polyadd(c, [-K_TARGET])) if abs(r.imag) < 1e-9 and 0.02 < r.real < 0.6]
    if not roots:  # fall back to linear extrapolation
        c1 = np.polyfit(xs, ks, 1)
        return float((K_TARGET - c1[1]) / c1[0]), c.tolist()
    return float(min(roots, key=lambda r: abs(r - np.mean(xs)))), c.tolist()


def run_case(case: str, scan=None, log=print) -> dict:
    d = DESIGNS[case]
    T = d["T_rep"]
    part = HERE / "results" / f"neutronics_{case}.partial.json"
    prev = json.loads(part.read_text()) if part.exists() else {}
    out = {"case": case, "title": d["title"], "assumptions": d["assumptions"], "T_rep_K": T,
           "stats": STAT, "scan_stats": SCAN_STAT, "scan": []}
    save = lambda: part.write_text(json.dumps(out, indent=1))
    t0 = time.time()
    done_x = {round(s["pu_frac"], 4): s for s in prev.get("scan", [])}
    for x in scan or SCAN.get(case, DEFAULT_SCAN):
        if round(x, 4) in done_x:
            out["scan"].append(done_x[round(x, 4)])
            continue
        r = screen_plus(d["build"](x), T, label=f"{case} x={x}", **SCAN_STAT)
        out["scan"].append({"pu_frac": x, "k_inf": r["k_inf"], "sd": r["k_inf_sd"], "CR": r["conversion_ratio"]})
        log(f"{case} x={x:.3f} k={r['k_inf']:.4f}+-{r['k_inf_sd']:.4f} CR={r['conversion_ratio']:.3f} ({time.time()-t0:.0f}s)")
        save()
    xs = [s["pu_frac"] for s in out["scan"]]
    ks = [s["k_inf"] for s in out["scan"]]
    xstar, coef = solve_x(xs, ks)
    xstar = round(xstar, 4)
    out["fit_coef_quadratic"] = coef
    out["pu_frac_at_k1.15"] = xstar
    if prev.get("at_target") and abs(prev.get("pu_frac_at_k1.15", -1) - xstar) < 1e-9:
        base = prev["at_target"]
    else:
        base = screen_plus(d["build"](xstar), T, label=f"{case} x*={xstar}", **STAT)
    out["at_target"] = base
    save()
    log(f"{case} x*={xstar} k={base['k_inf']:.4f} CR={base['conversion_ratio']:.3f} Emed={base['median_energy_eV']:.3g} eV")
    # coolant void worth: coolant to zero density, other volumes fixed (as infinite.void_worth)
    light = d.get("light", False)  # light cases: scan + target point + variants only
    ci = d["coolant_index"]
    if prev.get("void"):
        out["void"] = prev["void"]
    elif ci is not None and not light:
        comps = d["build"](xstar)
        frac = comps[ci][1]
        comps = [c for i, c in enumerate(comps) if i != ci] + [(void(), frac)]
        pert = screen_plus(comps, T, label=f"{case} voided", **STAT)
        w, sd = worth_pcm(base["k_inf"], base["k_inf_sd"], pert["k_inf"], pert["k_inf_sd"])
        out["void"] = {"k_inf": pert["k_inf"], "sd": pert["k_inf_sd"], "worth_pcm": w, "worth_sd_pcm": sd,
                       "median_energy_eV": pert["median_energy_eV"], "CR": pert["conversion_ratio"]}
        log(f"{case} void worth {w:+.0f} +- {sd:.0f} pcm")
        save()
    # temperature effect 1200 vs 2100 K (whole homogenised medium, so Doppler plus coolant data broadening)
    temps = {}
    for Tt in ((1200.0, 2100.0) if not (light or prev.get("temperature")) else ()):
        if abs(Tt - T) < 1e-6:
            temps[Tt] = (base["k_inf"], base["k_inf_sd"])
        else:
            r = screen_plus(d["build"](xstar), Tt, label=f"{case} T={Tt}", **STAT)
            temps[Tt] = (r["k_inf"], r["k_inf_sd"])
    if prev.get("temperature"):
        out["temperature"] = prev["temperature"]
    elif light:
        temps = None
    else:
      w, sd = worth_pcm(temps[1200.0][0], temps[1200.0][1], temps[2100.0][0], temps[2100.0][1])
      out["temperature"] = {"k_1200": temps[1200.0][0], "sd_1200": temps[1200.0][1], "k_2100": temps[2100.0][0],
                          "sd_2100": temps[2100.0][1], "dk_pcm_1200_to_2100": w, "sd_pcm": sd,
                          "pcm_per_K": w / 900.0,
                          "doppler_constant_pcm": w / np.log(2100 / 1200)}
      log(f"{case} 1200->2100 K: {w:+.0f} +- {sd:.0f} pcm")
    out["variants"] = {}
    save()
    for name, kw in d["variants"].items():
        if name in prev.get("variants", {}):
            out["variants"][name] = prev["variants"][name]
            continue
        r = screen_plus(d["build"](xstar, **kw), T, label=f"{case} {name}", **STAT)
        w, sd = worth_pcm(base["k_inf"], base["k_inf_sd"], r["k_inf"], r["k_inf_sd"])
        out["variants"][name] = {"k_inf": r["k_inf"], "sd": r["k_inf_sd"], "CR": r["conversion_ratio"],
                                 "dk_pcm": w, "sd_pcm": sd, "median_energy_eV": r["median_energy_eV"],
                                 "parasitic_absorption_share": r["parasitic_absorption_share"],
                                 "tritium_per_fission": r["tritium_per_fission"],
                                 "np_per_fission": r["np_per_fission"]}
        log(f"{case} variant {name}: k={r['k_inf']:.4f} ({w:+.0f} pcm) CR={r['conversion_ratio']:.3f}")
        save()
    out["runtime_s"] = time.time() - t0
    return out


def main(cases):
    for case in cases:
        res = run_case(case, log=lambda s: print(s, flush=True))
        (HERE / "results" / f"neutronics_{case}.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])

"""Infinite-medium neutronics screen of the new geometry candidates (analysis/common/infinite.py).

For each case: find the Pu/(U+Pu) giving k_inf = 1.15 by secant search, report the conversion-ratio
proxy there, and (where the coolant is not a gas) the coolant-void worth at that Pu fraction.
Volume fractions come from thermal.py geometry (see README). Results accumulate in
results/neutronics.json, so the script can be re-run to resume.

Run: python neutronics.py [case ...]      (threads=1; bracketing runs 10k x 40, final runs 20k x 60)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "analysis" / "common"))
import materials as M  # noqa: E402
from infinite import screen  # noqa: E402

RES = HERE / "results" / "neutronics.json"
TARGET = 1.15
BRACKET = dict(particles=10000, batches=40, inactive=15, threads=1)
FINAL = dict(particles=20000, batches=60, inactive=20, threads=1)

# volume fractions (thermal.py geometry); T in K. coolant: index of the coolant component, or None.
def CASES():
    UPu, UN = M.upu_liquid, M.upun
    return {
        "A2_ref": dict(T=2100, guess=(0.10, 0.14), coolant=3, desc="A2 reference: 66.8% liquid U-Pu, W 10.6%, AlN 3.0%, Al 19.6%",
                       comps=lambda pu: [(UPu(pu), .668), (M.W(), .106), (M.AlN(), .030), (M.Al(), .196)]),
        "L7_tube_Al": dict(T=2100, guess=(0.12, 0.17), coolant=3, desc="L7 reference: W fuel tubes r 10 mm in rows between AlN/Al panels, vacuum gap",
                           comps=lambda pu: [(UPu(pu), .4268), (M.W(), .0896), (M.AlN(), .0625), (M.Al(), .1250), (M.vacuum(), .2961)]),
        "L7_tube_Pb": dict(T=2100, guess=(0.12, 0.17), coolant=3, desc="L7, Pb in Mo panels",
                           comps=lambda pu: [(UPu(pu), .4268), (M.W(), .0896), (M.Mo(), .0625), (M.Pb(), .1250), (M.vacuum(), .2961)]),
        "L7_tube_He": dict(T=2100, guess=(0.12, 0.17), coolant=None, desc="L7, He (7 MPa) in Mo panels",
                           comps=lambda pu: [(UPu(pu), .4268), (M.W(), .0896), (M.Mo(), .0625), (M.He(), .1250), (M.vacuum(), .2961)]),
        "L7_plate20_Al": dict(T=2100, guess=(0.10, 0.15), coolant=3, desc="L7 plates: 20 mm fuel slab, 1 mm W cans, AlN/Al panels",
                              comps=lambda pu: [(UPu(pu), .625), (M.W(), .0625), (M.AlN(), .0625), (M.Al(), .125), (M.vacuum(), .125)]),
        "L7_plate40_Al": dict(T=2100, guess=(0.10, 0.14), coolant=None, desc="L7 plates: 40 mm fuel slab",
                              comps=lambda pu: [(UPu(pu), .7692), (M.W(), .0385), (M.AlN(), .0385), (M.Al(), .0769), (M.vacuum(), .0769)]),
        "S9_UN_Al": dict(T=2100, guess=(0.12, 0.17), coolant=3, desc="S9: (U,Pu)N 14 mm plates in 0.5 mm W, vacuum gap, AlN/Al panels",
                         comps=lambda pu: [(UN(pu), .56), (M.W(), .04), (M.AlN(), .08), (M.Al(), .16), (M.vacuum(), .16)]),
        "S5_bed_He": dict(T=1500, guess=(0.13, 0.18), coolant=None, desc="S5: (U,Pu)N kernels + ZrN coat, bed solids 0.50, He 7 MPa, Mo structure",
                          comps=lambda pu: [(UN(pu), .43), (M.ZrN(), .07), (M.He(), .45), (M.Mo(), .05)]),
        "S6_lattice_He": dict(T=1500, guess=(0.13, 0.18), coolant=None, desc="S6: printed (U,Pu)N-Mo cermet lattice (70/30), solid 0.60, He 0.40",
                              comps=lambda pu: [(UN(pu), .42), (M.Mo(), .18), (M.He(), .40)]),
        "S8_particles": dict(T=1500, guess=(0.16, 0.22), coolant=2, desc="S8: (U,Pu)N pins in Mo, falling Al2O3 particles (packing 0.58) in channels",
                             comps=lambda pu: [(UN(pu), .2974), (M.Mo(), .0790), (M.Al2O3(), .3617), (M.He(1e-4), .2619)]),
        "L3_pins_Al": dict(T=2100, guess=(0.13, 0.18), coolant=3, desc="L3: liquid U-Pu pins 9 mm bore, 0.8 mm W + 0.3 mm AlN, Al coolant, p/d 1.12",
                           comps=lambda pu: [(UPu(pu), .4668), (M.W(), .1807), (M.AlN(), .0754), (M.Al(), .2771)]),
        "L3_pins_Pb": dict(T=2100, guess=(0.13, 0.18), coolant=2, desc="L3: liquid U-Pu pins 9 mm bore, 0.8 mm W, Pb coolant, p/d 1.12",
                           comps=lambda pu: [(UPu(pu), .5212), (M.W(), .2018), (M.Pb(), .2770)]),
        "L5_film_Al": dict(T=2100, guess=(0.16, 0.22), coolant=3, desc="L5: 2 mm U-Pu films on both faces of W/AlN/Al panels, 3 mm gas space",
                           comps=lambda pu: [(UPu(pu), .2857), (M.W(), .1714), (M.AlN(), .0429), (M.Al(), .2857), (M.vacuum(), .2143)]),
    }


def load():
    return json.loads(RES.read_text()) if RES.exists() else {}


def save(d):
    RES.write_text(json.dumps(d, indent=1))


def run(case, pu, stats, label):
    c = CASES()[case]
    t0 = time.time()
    r = screen(c["comps"](pu), c["T"], label=label, **stats)
    r["pu_frac"] = pu
    r["wall_s"] = time.time() - t0
    r["stats"] = stats
    print(f"  {label}: Pu {pu:.4f} k {r['k_inf']:.4f}+-{r['k_inf_sd']:.4f} CR {r['conversion_ratio']:.3f} "
          f"E50 {r['median_energy_eV']/1e3:.0f} keV ({r['wall_s']:.0f} s)", flush=True)
    return r


def secant(p1, k1, p2, k2):
    return min(0.45, max(0.03, p2 + (TARGET - k2) * (p2 - p1) / (k2 - k1)))


def do_case(case, data):
    c = CASES()[case]
    d = data.get(case, {"desc": c["desc"], "T_K": c["T"], "runs": []})
    data[case] = d
    runs = d["runs"]
    print(case, c["desc"], flush=True)
    for g in c["guess"]:
        if not any(abs(r["pu_frac"] - g) < 1e-9 for r in runs):
            runs.append(run(case, g, BRACKET, f"{case} bracket")); save(data)
    for _ in range(2):  # at most two final iterations
        pts = sorted(runs, key=lambda r: abs(r["k_inf"] - TARGET))[:2]
        p = secant(pts[1]["pu_frac"], pts[1]["k_inf"], pts[0]["pu_frac"], pts[0]["k_inf"])
        fin = [r for r in runs if r["stats"] == FINAL and abs(r["k_inf"] - TARGET) < 0.012]
        if fin:
            break
        runs.append(run(case, round(p, 4), FINAL, f"{case} final")); save(data)
    fin = min((r for r in runs if r["stats"] == FINAL), key=lambda r: abs(r["k_inf"] - TARGET))
    # Pu fraction and CR at exactly k = 1.15: linear interpolation with the nearest other point
    other = min((r for r in runs if r is not fin), key=lambda r: abs(r["k_inf"] - TARGET))
    slope = (fin["k_inf"] - other["k_inf"]) / (fin["pu_frac"] - other["pu_frac"])
    pu_t = fin["pu_frac"] + (TARGET - fin["k_inf"]) / slope
    cr_slope = (fin["conversion_ratio"] - other["conversion_ratio"]) / (fin["pu_frac"] - other["pu_frac"])
    d["pu_at_1.15"] = pu_t
    d["cr_at_1.15"] = fin["conversion_ratio"] + cr_slope * (pu_t - fin["pu_frac"])
    d["dk_dPu"] = slope
    d["final"] = {k: fin[k] for k in ("pu_frac", "k_inf", "k_inf_sd", "conversion_ratio", "median_energy_eV",
                                      "parasitic_absorption_share")}
    if c["coolant"] is not None and "void" not in d:
        comps = c["comps"](fin["pu_frac"])
        i = c["coolant"]
        removed = comps[i][1]
        comps = [(m, 0.0 if j == i else f) for j, (m, f) in enumerate(comps) if j != i] + [(M.vacuum(), removed)]
        t0 = time.time()
        v = screen(comps, c["T"], label=f"{case} coolant voided", **FINAL)
        rho = lambda k: (k - 1) / k
        sd = 1e5 * ((v["k_inf_sd"] / v["k_inf"] ** 2) ** 2 + (fin["k_inf_sd"] / fin["k_inf"] ** 2) ** 2) ** 0.5
        d["void"] = {"k_inf": v["k_inf"], "k_inf_sd": v["k_inf_sd"], "conversion_ratio": v["conversion_ratio"],
                     "median_energy_eV": v["median_energy_eV"],
                     "worth_pcm": 1e5 * (rho(v["k_inf"]) - rho(fin["k_inf"])), "worth_sd_pcm": sd,
                     "wall_s": time.time() - t0}
        print(f"  void: k {v['k_inf']:.4f} worth {d['void']['worth_pcm']:.0f} +- {sd:.0f} pcm", flush=True)
    d["library_notes"] = sorted(M.LIBRARY_NOTES)
    save(data)


if __name__ == "__main__":
    names = sys.argv[1:] or list(CASES())
    data = load()
    for n in names:
        do_case(n, data)

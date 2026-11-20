"""Family A Phase 1 neutronics: infinite homogenised media with analysis/common/infinite.screen.

Stages (results cached in results/neutronics_cases.json, so a rerun only computes missing cases):
  1. Pu/(U+Pu) scans for A1 (ZrB2 clad, ~1600 K), A2 (reference W/AlN tubes, 2100 K) and A3 (Al-U-Pu
     solution at two heavy-metal atom fractions, 2100 K).
  2. Interpolate the Pu fraction giving k_inf = 1.15 (quadratic through the scan points), round it to
     0.0025, and run the perturbation cases there: coolant void, temperature, isotopes, cladding/wall
     variants and Na/Pb in place of Al at equal volume fraction (Q-033).

Run:  export PATH=/opt/mamba/envs/nuc/bin:$PATH
      python analysis/a-family/neutronics.py --workers 2            # all stages
      python analysis/a-family/neutronics.py --stage 1               # scans only
Statistics: 20,000 particles x 60 batches (20 inactive), threads=1 per case.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "analysis" / "common"))

import materials as M  # noqa: E402
from geometry import A1_FRACTIONS, A2_FRACTIONS  # noqa: E402

RESULTS = HERE / "results" / "neutronics_cases.json"
TARGET_K = 1.15
STATS = dict(particles=20000, batches=60, inactive=20, threads=1)

B11_NATURAL = 0.8035  # B-11 atom fraction in natural boron (db: IAEA LiveChart 80.35%)
N15_NATURAL = 0.003795  # N-15 atom fraction in natural nitrogen (db: IAEA LiveChart 0.3795%)

SCANS = {
    "A1": [0.10, 0.14, 0.18],
    "A2": [0.08, 0.12, 0.16],
    "A3x33": [0.20, 0.30, 0.40],
    "A3x20": [0.25, 0.40, 0.55],
}


# ----------------------------------------------------------------------------- case builders
def a1(pu, T=1600.0, clad="ZrB2", b11=0.999, n15_fuel=0.999, n15_aln=0.999, coolant="Al", void=False):
    f = A1_FRACTIONS[clad]
    comps = [(M.upu_nitride(pu, n15=n15_fuel), f["fuel"])]
    if clad == "ZrB2":
        comps.append((M.zrb2(b11), f["ZrB2"]))
    else:
        comps += [(M.tungsten(), f["W"]), (M.aln(n15_aln), f["AlN"])]
    comps.append((M.void_filler(), f["gap"]))
    cool = {"Al": lambda: M.aluminium(M.DENSITY["Al_1600K"]), "Na": M.sodium, "Pb": M.lead}[coolant]()
    comps.append((M.void_filler() if void else cool, f["coolant"]))
    return comps, T


def a2(pu, T=2100.0, wall="W/AlN", b11=0.999, n15_aln=0.999, coolant="Al", void=False):
    f = A2_FRACTIONS[wall]
    comps = [(M.upu_liquid(pu), f["fuel"])]
    if wall == "ZrB2":
        comps.append((M.zrb2(b11), f["ZrB2"]))
    else:
        comps += [(M.tungsten(), f["W"]), (M.aln(n15_aln), f["AlN"])]
    cool = {"Al": lambda: M.aluminium(M.DENSITY["Al_2100K"]), "Na": M.sodium, "Pb": M.lead}[coolant]()
    comps.append((M.void_filler() if void else cool, f["coolant"]))
    return comps, T


def a3(pu, x_hm, T=2100.0, structure=0.0, b11=0.999):
    comps = [(M.al_u_pu_solution(x_hm, pu), 1.0 - structure)]
    if structure:
        comps.append((M.zrb2(b11), structure))
    return comps, T


BUILDERS = {"A1": a1, "A2": a2, "A3": a3}


def case_spec(design: str, **kw) -> dict:
    return {"design": design, "kw": kw}


def run_case(name: str, spec: dict) -> tuple[str, dict]:
    from infinite import screen
    comps, T = BUILDERS[spec["design"]](**spec["kw"])
    res = screen(comps, T, label=name, **STATS)
    res["spec"] = spec
    return name, res


# ----------------------------------------------------------------------------- stages
def stage1_cases() -> dict:
    cases = {}
    for pu in SCANS["A1"]:
        cases[f"A1_scan_pu{pu:.3f}"] = case_spec("A1", pu=pu)
    for pu in SCANS["A2"]:
        cases[f"A2_scan_pu{pu:.3f}"] = case_spec("A2", pu=pu)
    for pu in SCANS["A3x33"]:
        cases[f"A3x33_scan_pu{pu:.3f}"] = case_spec("A3", pu=pu, x_hm=1 / 3)
    for pu in SCANS["A3x20"]:
        cases[f"A3x20_scan_pu{pu:.3f}"] = case_spec("A3", pu=pu, x_hm=0.20)
    return cases


def critical_pu(db: dict, prefix: str) -> dict:
    pts = sorted((v["spec"]["kw"]["pu"], v["k_inf"]) for k, v in db.items() if k.startswith(prefix + "_scan_"))
    x, y = np.array(pts).T
    c = np.polyfit(x, y, min(2, len(x) - 1))
    grid = np.linspace(0.0, 0.9, 9001)
    kk = np.polyval(c, grid)
    ok = np.where(np.diff(np.sign(kk - TARGET_K)) != 0)[0]
    pu_star = float(grid[ok[0]]) if len(ok) else float("nan")
    slope = float(np.polyval(np.polyder(c), pu_star)) if len(ok) else float("nan")
    return {"pu_exact": pu_star, "pu": round(pu_star / 0.0025) * 0.0025, "dk_dpu": slope,
            "scan": [[float(a), float(b)] for a, b in pts], "extrapolated": bool(pu_star > x.max() or pu_star < x.min())}


def stage2_cases(crit: dict) -> dict:
    c = {}
    p1, p2 = crit["A1"]["pu"], crit["A2"]["pu"]
    # A1 (ZrB2 cladding reference, 1600 K)
    c["A1_ref"] = case_spec("A1", pu=p1)
    c["A1_void"] = case_spec("A1", pu=p1, void=True)
    c["A1_T1200"] = case_spec("A1", pu=p1, T=1200.0)
    c["A1_T2100"] = case_spec("A1", pu=p1, T=2100.0)
    c["A1_Bnat"] = case_spec("A1", pu=p1, b11=B11_NATURAL)
    c["A1_B995"] = case_spec("A1", pu=p1, b11=0.995)
    c["A1_Nnat_fuel"] = case_spec("A1", pu=p1, n15_fuel=N15_NATURAL)
    c["A1_WAlN"] = case_spec("A1", pu=p1, clad="W/AlN")
    c["A1_WAlN_void"] = case_spec("A1", pu=p1, clad="W/AlN", void=True)
    c["A1_WAlN_Nnat"] = case_spec("A1", pu=p1, clad="W/AlN", n15_aln=N15_NATURAL)
    for cool in ("Na", "Pb"):
        c[f"A1_{cool}"] = case_spec("A1", pu=p1, coolant=cool)
        c[f"A1_{cool}_void"] = case_spec("A1", pu=p1, coolant=cool, void=True)
    # A2 (reference W/AlN wall, 2100 K)
    c["A2_ref"] = case_spec("A2", pu=p2)
    c["A2_void"] = case_spec("A2", pu=p2, void=True)
    c["A2_T1200"] = case_spec("A2", pu=p2, T=1200.0)
    c["A2_AlN_Nnat"] = case_spec("A2", pu=p2, n15_aln=N15_NATURAL)
    c["A2_ZrB2"] = case_spec("A2", pu=p2, wall="ZrB2")
    c["A2_ZrB2_Bnat"] = case_spec("A2", pu=p2, wall="ZrB2", b11=B11_NATURAL)
    c["A2_ZrB2_void"] = case_spec("A2", pu=p2, wall="ZrB2", void=True)
    for cool in ("Na", "Pb"):
        c[f"A2_{cool}"] = case_spec("A2", pu=p2, coolant=cool)
        c[f"A2_{cool}_void"] = case_spec("A2", pu=p2, coolant=cool, void=True)
    # A3 (solution; uniform density changes do not alter k_inf of a single homogeneous medium)
    for tag, x in (("A3x33", 1 / 3), ("A3x20", 0.20)):
        p = crit[tag]["pu"]
        if np.isfinite(p) and p <= 0.9:
            c[f"{tag}_ref"] = case_spec("A3", pu=p, x_hm=x)
            c[f"{tag}_T1200"] = case_spec("A3", pu=p, x_hm=x, T=1200.0)
    c["A3x33_ZrB2_10pct"] = case_spec("A3", pu=crit["A3x33"]["pu"], x_hm=1 / 3, structure=0.10)
    return c


def load() -> dict:
    return json.loads(RESULTS.read_text()) if RESULTS.exists() else {}


def run_all(cases: dict, workers: int) -> dict:
    db = load()
    todo = {k: v for k, v in cases.items() if k not in db or db[k].get("spec") != v}
    print(f"{len(todo)} cases to run ({len(cases) - len(todo)} cached)", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(run_case, k, v) for k, v in todo.items()]
        for f in as_completed(futs):
            name, res = f.result()
            db = load()
            db[name] = res
            RESULTS.write_text(json.dumps(db, indent=1, sort_keys=True))
            print(f"{name}: k_inf={res['k_inf']:.5f}+-{res['k_inf_sd']:.5f} CR={res['conversion_ratio']:.3f} "
                  f"E50={res['median_energy_eV']/1e3:.0f} keV", flush=True)
    return load()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--stage", type=int, default=0, help="1 or 2; 0 = both")
    a = ap.parse_args()
    if a.stage in (0, 1):
        run_all(stage1_cases(), a.workers)
    if a.stage in (0, 2):
        db = load()
        crit = {t: critical_pu(db, t) for t in ("A1", "A2", "A3x33", "A3x20")}
        (HERE / "results" / "critical_pu.json").write_text(json.dumps(crit, indent=1))
        print(json.dumps(crit, indent=1))
        run_all(stage2_cases(crit), a.workers)


if __name__ == "__main__":
    main()

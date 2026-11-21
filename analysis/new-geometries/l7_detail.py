"""L7 / R-family detail neutronics (higher statistics), after neutronics.py has run the L7 cases.

1. R1 reference at the L7_tube_Al Pu fraction with 50,000 particles x 100 batches (30 inactive),
   gap filled with N2 at ~1 bar (R1 choice) instead of vacuum.
2. Gap worths relative to that reference: gap evacuated (vacuum), gap flooded with Al (receiver breach),
   gap flooded with Pb (R2 receiver breach, Pb composition otherwise R1).
3. Coolant (Al) voided, at the same statistics.
Results to results/l7_detail.json (written after each run).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import openmc

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "analysis" / "common"))
import materials as M  # noqa: E402
from infinite import screen  # noqa: E402

RES = HERE / "results" / "l7_detail.json"
HI = dict(particles=50000, batches=100, inactive=30, threads=1)
F = {"fuel": .4268, "can": .0896, "panel": .0625, "cool": .1250, "gap": .2961}


def n2_gas():
    m = openmc.Material(name="N2 1 bar ~1,900 K")
    m.add_nuclide("N14", 0.99636); m.add_nuclide("N15", 0.00364)   # natural N in the gap gas
    m.set_density("g/cm3", 1e5 * 0.028 / (8.314 * 1900) / 1000)      # ~1.8e-4 g/cm3
    return m


def comps(pu, gap=None, cool=None):
    return [(M.upu_liquid(pu), F["fuel"]), (M.W(), F["can"]), (M.AlN(), F["panel"]),
            (cool if cool is not None else M.Al(), F["cool"]), (gap if gap is not None else n2_gas(), F["gap"])]


def main():
    nj = json.loads((HERE / "results" / "neutronics.json").read_text())
    pu = round(nj["L7_tube_Al"]["pu_at_1.15"], 4)
    out = json.loads(RES.read_text()) if RES.exists() else {}
    out["pu_frac"] = pu
    out["stats"] = HI
    cases = {
        "R1_reference_N2_gap": lambda: comps(pu),
        "gap_vacuum": lambda: comps(pu, gap=M.vacuum()),
        "gap_flooded_Al": lambda: comps(pu, gap=M.Al()),
        "coolant_voided": lambda: comps(pu, cool=M.vacuum()),
        "gap_flooded_Pb": lambda: comps(pu, gap=M.Pb()),
    }
    rho = lambda k: (k - 1) / k
    only = sys.argv[1:]
    for name, f in cases.items():
        if name in out or (only and name not in only):
            continue
        t0 = time.time()
        r = screen(f(), 2100, label=name, **HI)
        out[name] = {k: r[k] for k in ("k_inf", "k_inf_sd", "conversion_ratio", "median_energy_eV",
                                       "parasitic_absorption_share")}
        out[name]["wall_s"] = time.time() - t0
        if name != "R1_reference_N2_gap":
            b = out["R1_reference_N2_gap"]
            out[name]["worth_pcm"] = 1e5 * (rho(r["k_inf"]) - rho(b["k_inf"]))
            out[name]["worth_sd_pcm"] = 1e5 * ((r["k_inf_sd"] / r["k_inf"] ** 2) ** 2 + (b["k_inf_sd"] / b["k_inf"] ** 2) ** 2) ** 0.5
        cur = json.loads(RES.read_text()) if RES.exists() else {}
        cur.update({k: v for k, v in out.items() if k in (name, "pu_frac", "stats", "R1_reference_N2_gap")})
        out = cur
        RES.write_text(json.dumps(out, indent=1))
        print(name, json.dumps({k: v for k, v in out[name].items() if k != "parasitic_absorption_share"}), flush=True)


if __name__ == "__main__":
    main()

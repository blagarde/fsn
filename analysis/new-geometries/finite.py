"""Finite-core check: does the larger L7 core still breed? Compared with A2 at its own size.

Homogenised cylinder (H = D) of the case composition, volume from thermal.py, inside a 40 cm
blanket of the same cell structure filled with depleted U (Pu = 0), vacuum outside. Finds the
Pu/(U+Pu) for k_eff = 1.00 (clean, no control margin) by interpolation between two runs and
reports the breeding-ratio proxy (fertile captures / fissile absorptions, core + blanket).
Still a screening model: no reflector design, no burnup, homogenised (no self-shielding).

Run: python finite.py [case ...]
"""
from __future__ import annotations

import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path

import openmc

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "analysis" / "common"))
import materials as M  # noqa: E402
from infinite import XS, FISSILE, FERTILE, _settings  # noqa: E402
from neutronics import CASES  # noqa: E402

RES = HERE / "results" / "finite.json"
BLANKET = 40.0  # cm
SIZES = {"A2_ref": 3.3, "L7_tube_Al": None, "L7_plate20_Al": None}   # m3; None -> from thermal.json


def core_volume(case):
    if SIZES.get(case):
        return SIZES[case]
    th = json.loads((HERE / "results" / "thermal.json").read_text())["L7"]
    if case == "L7_tube_Al":
        return next(t for t in th["tube_sweep"] if t["r_i_mm"] == 10.0 and t["Th_C"] == 2000 and t["eps_container"] == 0.8)["core_volume_m3"]
    return next(s for s in th["slab_sweep"] if s["t_fuel_mm"] == 20 and s["Th_C"] == 2000 and s["Tout_C"] == 1500
                and s["eps_container"] == 0.8)["core_volume_m3"]


def run(case, pu, particles=20000, batches=60, inactive=20):
    c = CASES()[case]
    T = c["T"]
    def mix(p, name):
        comps = c["comps"](p)
        fr = [f for _, f in comps]
        m = openmc.Material.mix_materials([x for x, _ in comps], [f / sum(fr) for f in fr], "vo")
        m.temperature, m.name = T, name
        return m
    core_m, blk_m = mix(pu, "core"), mix(0.0, "blanket")
    V = core_volume(case) * 1e6  # cm3
    R = (V / (2 * math.pi)) ** (1 / 3)      # H = 2R
    H = 2 * R
    c_in = openmc.ZCylinder(r=R)
    c_out = openmc.ZCylinder(r=R + BLANKET, boundary_type="vacuum")
    z = [openmc.ZPlane(z0=v) for v in (-H / 2 - BLANKET, -H / 2, H / 2, H / 2 + BLANKET)]
    z[0].boundary_type = z[3].boundary_type = "vacuum"
    core = openmc.Cell(fill=core_m, region=-c_in & +z[1] & -z[2])
    blk = openmc.Cell(fill=blk_m, region=-c_out & +z[0] & -z[3] & ~(-c_in & +z[1] & -z[2]))
    for cell in (core, blk):
        cell.temperature = T
    nucs = sorted(set(core_m.get_nuclide_atom_densities()) | set(blk_m.get_nuclide_atom_densities()))
    tal = openmc.Tally(name="rates")
    tal.filters = [openmc.CellFilter([core, blk])]
    tal.nuclides = [n for n in nucs if n in FISSILE + FERTILE]
    tal.scores = ["absorption", "fission"]
    s = _settings(T, particles, batches, inactive)
    s.source = openmc.IndependentSource(space=openmc.stats.Box((-R / 2, -R / 2, -H / 4), (R / 2, R / 2, H / 4)))
    model = openmc.Model(openmc.Geometry([core, blk]), openmc.Materials([core_m, blk_m]), s, openmc.Tallies([tal]))
    model.materials.cross_sections = str(XS)
    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        cwd = os.getcwd(); os.chdir(tmp)
        try:
            sp_path = model.run(threads=1, output=False)
            with openmc.StatePoint(sp_path) as sp:
                k = sp.keff
                t = sp.get_tally(name="rates")
                def val(cell, nuc, score):
                    return float(t.get_values(filters=[openmc.CellFilter], filter_bins=[(cell.id,)],
                                              nuclides=[nuc], scores=[score]).ravel()[0])
                out = {}
                for cell, tag in ((core, "core"), (blk, "blanket")):
                    fis = sum(val(cell, n, "absorption") for n in tal.nuclides if n in FISSILE)
                    fer = sum(val(cell, n, "absorption") - val(cell, n, "fission") for n in tal.nuclides if n in FERTILE)
                    out[tag] = {"fissile_abs": fis, "fertile_capture": fer}
        finally:
            os.chdir(cwd)
    fis = out["core"]["fissile_abs"] + out["blanket"]["fissile_abs"]
    fer = out["core"]["fertile_capture"] + out["blanket"]["fertile_capture"]
    r = {"pu_frac": pu, "k_eff": float(k.nominal_value), "k_sd": float(k.std_dev), "BR_total": fer / fis,
         "CR_core": out["core"]["fertile_capture"] / out["core"]["fissile_abs"],
         "blanket_share_of_fertile_capture": out["blanket"]["fertile_capture"] / fer,
         "core_volume_m3": V / 1e6, "R_cm": R, "H_cm": H, "wall_s": time.time() - t0}
    print(f"  {case}: Pu {pu:.3f} k_eff {r['k_eff']:.4f}+-{r['k_sd']:.4f} BR {r['BR_total']:.3f} "
          f"CR_core {r['CR_core']:.3f} ({r['wall_s']:.0f} s)", flush=True)
    return r


if __name__ == "__main__":
    data = json.loads(RES.read_text()) if RES.exists() else {}
    inf = json.loads((HERE / "results" / "neutronics.json").read_text())
    for case in sys.argv[1:] or ["A2_ref", "L7_tube_Al"]:
        p0 = inf[case]["pu_at_1.15"]
        d = data.setdefault(case, {"runs": []})
        for p in (round(p0 * 0.85, 4), round(p0 * 1.0, 4)):
            if not any(abs(x["pu_frac"] - p) < 1e-9 for x in d["runs"]):
                d["runs"].append(run(case, p)); RES.write_text(json.dumps(data, indent=1))
        a, b = d["runs"][-2:]
        sl = (b["k_eff"] - a["k_eff"]) / (b["pu_frac"] - a["pu_frac"])
        pc = b["pu_frac"] + (1.0 - b["k_eff"]) / sl
        f = (pc - a["pu_frac"]) / (b["pu_frac"] - a["pu_frac"])
        d["pu_critical"] = pc
        d["BR_at_critical"] = a["BR_total"] + f * (b["BR_total"] - a["BR_total"])
        d["CR_core_at_critical"] = a["CR_core"] + f * (b["CR_core"] - a["CR_core"])
        d["note"] = "clean critical (k_eff 1.00), homogenised core + 40 cm depleted-U blanket of the same cell structure, vacuum outside"
        RES.write_text(json.dumps(data, indent=1))
        print(case, json.dumps({k: v for k, v in d.items() if k != "runs"}), flush=True)

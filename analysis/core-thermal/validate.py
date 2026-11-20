"""Checks of the one-group core model against OpenMC transport and a benchmark.

  1. Godiva (ICSBEP HEU-MET-FAST-001): bare HEU sphere, critical radius 8.7407 cm.
  2. k_inf and conversion ratio of each reference case: one-group model vs direct OpenMC
     (analysis/common/infinite.py) on the same homogenised composition.
  3. Finite reflected cylinders sized by the model's design mode (1,000 MWth): OpenMC k_eff should
     come out near 1 if the model's leakage (diffusion + reflector savings) is right.
  4. Elastic P1: data-derived (p1data.py) vs analog tally for the nuclides present in each reference.

Run: /opt/mamba/envs/nuc/bin/python validate.py [godiva infinite finite p1]  -> results/validation.json
"""
from __future__ import annotations

import dataclasses
import json
import math
import os
import sys
import tempfile
from pathlib import Path

import openmc

import cases as CS
import core
import neutronics as N

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "common"))
from infinite import screen  # noqa: E402

OUT = HERE / "results" / "validation.json"
XS = HERE.parents[1] / "data" / "openmc" / "cross_sections.xml"


def godiva():
    m = openmc.Material(name="Godiva HEU")
    for nuc, w in (("U234", 0.0102), ("U235", 0.9371), ("U238", 0.0527)):
        m.add_nuclide(nuc, w, "wo")
    m.set_density("g/cm3", 18.74)
    g = N.one_group(N.Region().add("fuel", m, 1.0, 1200.0))
    R = N.bare_sphere_radius(g)
    return {"benchmark_R_cm": 8.7407, "model_R_cm": R, "error_pct": 100 * (R / 8.7407 - 1), "k_inf": g.k_inf,
            "spectrum_note": g.note,
            "comment": "one-group diffusion in a 9 cm sphere (~3 transport mean free paths) is outside its validity; "
                       "this bounds the model's leakage error for small cores"}


def infinite(names, particles=6000, batches=40, inactive=15):
    out = {}
    for n in names:
        s = CS.CASES[n]
        st = core.solve(s)
        T_c = 0.5 * (s.T_in + s.T_out)
        reg = core.region(s, st.T_fuel_avg_K, T_c)
        T = min(max(st.T_fuel_avg_K, 1200.0), 2100.0)
        comps = [(m, f) for _, m, f, _ in reg.parts]
        r = screen(comps, T, particles=particles, batches=batches, inactive=inactive,
                   threads=int(os.environ.get("OMP_THREADS", "2")), label=n)
        g = N.one_group(N.Region(parts=[(ro, m, f, T) for ro, m, f, _ in reg.parts]))
        out[n] = {"T_K": T, "openmc_k_inf": r["k_inf"], "openmc_sd": r["k_inf_sd"], "model_k_inf": g.k_inf,
                  "dk_pcm": 1e5 * (g.k_inf - r["k_inf"]), "openmc_cr": r["conversion_ratio"], "model_cr": g.cr,
                  "openmc_median_E_eV": r["median_energy_eV"], "model_weights": g.weights}
        print(n, out[n], flush=True)
    return out


def finite(names, P_MW=1000.0, particles=8000, batches=50, inactive=20):
    """Homogenised cylinder + reflector (radial and axial) at the model's design-mode size."""
    out = {}
    for n in names:
        s = CS.CASES[n]
        if s.circulating:
            continue
        st = core.solve_for_power(s, P_MW)
        s2 = dataclasses.replace(s, pu=st.pu)
        T_c = 0.5 * (s.T_in + s.T_out)
        reg = core.region(s2, st.T_fuel_avg_K, T_c)
        mix = openmc.Material.mix_materials([m for _, m, _, _ in reg.parts], [f for _, _, f, _ in reg.parts], "vo")
        T = min(max(st.T_fuel_avg_K, 1200.0), 2100.0)
        mix.temperature = T
        rmat, rrho, rt = s.reflector
        refl = N.element_material(rmat, rrho)
        refl.temperature = min(max(T_c, 1200.0), 2100.0)
        R, H = st.R_m * 100, st.H_m * 100
        core_cyl = openmc.ZCylinder(r=R)
        out_cyl = openmc.ZCylinder(r=R + rt, boundary_type="vacuum")
        z0, z1 = openmc.ZPlane(-H / 2), openmc.ZPlane(H / 2)
        zb, zt = openmc.ZPlane(-H / 2 - rt, boundary_type="vacuum"), openmc.ZPlane(H / 2 + rt, boundary_type="vacuum")
        c_core = openmc.Cell(fill=mix, region=-core_cyl & +z0 & -z1)
        c_refl = openmc.Cell(fill=refl, region=-out_cyl & +zb & -zt & ~(-core_cyl & +z0 & -z1))
        geom = openmc.Geometry([c_core, c_refl])
        st_ = openmc.Settings()
        st_.particles, st_.batches, st_.inactive = particles, batches, inactive
        st_.source = openmc.IndependentSource(space=openmc.stats.Box((-R / 2, -R / 2, -H / 4), (R / 2, R / 2, H / 4)))
        st_.temperature = {"method": "interpolation", "default": T}
        st_.output = {"tallies": False, "summary": False}
        model = openmc.Model(geom, openmc.Materials([mix, refl]), st_)
        model.materials.cross_sections = str(XS)
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                sp = model.run(threads=int(os.environ.get("OMP_THREADS", "2")), output=False)
                with openmc.StatePoint(sp) as f:
                    k = f.keff
            finally:
                os.chdir(cwd)
        out[n] = {"P_MW": P_MW, "pu": st.pu, "R_cm": R, "H_cm": H, "reflector": s.reflector,
                  "model_k_eff": st.k_eff, "openmc_k_eff": float(k.nominal_value), "openmc_sd": float(k.std_dev),
                  "dk_pcm": 1e5 * (st.k_eff - float(k.nominal_value))}
        print(n, out[n], flush=True)
    return out


def p1():
    c = json.loads(N.CONSTANTS.read_text())
    rows = []
    for key, v in c.items():
        if key.startswith("_"):
            continue
        for nuc, d in v["sigma_b"].items():
            if d.get("present") and d.get("scatter_p1_analog"):
                rows.append({"run": key, "nuclide": nuc, "analog": d["scatter_p1_analog"], "data": d["scatter_p1_data"],
                             "ratio": d["scatter_p1_data"] / d["scatter_p1_analog"]})
    return rows


def main():
    what = sys.argv[1:] or ["godiva", "p1", "infinite", "finite"]
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    if "godiva" in what:
        res["godiva"] = godiva(); print(res["godiva"])
    if "p1" in what:
        res["p1"] = p1()
        for r in res["p1"]:
            if r["nuclide"] in ("U238", "Pu239", "Pb208", "Na23", "Al27", "O16", "N15", "Fe56", "W184"):
                print(r)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    if "infinite" in what:
        res["infinite"] = infinite([n for n in CS.CASES])
        OUT.write_text(json.dumps(res, indent=1))
    if "finite" in what:
        res["finite"] = finite(["MOX-Na", "UN-Pb", "UPu-Al-pool"])
        OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

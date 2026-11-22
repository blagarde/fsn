"""Void reactivity of a boiling fuel pool, by OpenMC (ENDF/B-VIII.0 library of this repository).

Vapour bubbles displace liquid fuel; fuel mass is conserved, so the liquid column swells upward
(density x (1 - alpha), height / (1 - alpha), radius fixed). The void worth is therefore a fuel-density
worth with a free surface, the same mechanism as liquid expansion in the core-thermal study.

Cases (Pu 15-30 %, reactor-grade vector, depleted U):
  chloride  NaCl-(U,Pu)Cl3 30/70 mol%, Cl-37 99 %, at 2,000 K (approx density from model.py)
  metal     liquid U-Pu (pool.py density) with a 20 cm W reflector
Writes results/void.json. Run: /opt/mamba/envs/nuc/bin/python neutronics.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import openmc

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "analysis" / "core-thermal"))
import neutronics as N  # noqa: E402  (core-thermal: materials, Pu vector)
import model as BM      # noqa: E402

XS = ROOT / "data" / "openmc" / "cross_sections.xml"
OUT = HERE / "results" / "void.json"


def chloride(pu, rho_gcc, cl37=0.99):
    m = openmc.Material(name=f"NaCl-(U,Pu)Cl3 pu {pu}")
    x_na = 0.30
    m.add_nuclide("Na23", x_na)
    N.M.heavy_metal(m, pu, atoms=1 - x_na)
    n_cl = x_na + 3 * (1 - x_na)
    m.add_nuclide("Cl37", n_cl * cl37)
    m.add_nuclide("Cl35", n_cl * (1 - cl37))
    m.set_density("g/cm3", rho_gcc)
    return m


def keff(fuel, R, H, refl=None, t_r=0.0, T=2000.0, particles=20000, batches=70, inactive=20):
    fuel.temperature = min(T, 2100.0)
    mats = [fuel]
    c_in, z0, z1 = openmc.ZCylinder(r=R), openmc.ZPlane(-H / 2), openmc.ZPlane(H / 2)
    core = -c_in & +z0 & -z1
    cells = [openmc.Cell(fill=fuel, region=core)]
    if refl is not None:
        refl.temperature = 1500.0
        mats.append(refl)
        c_out, zb, zt = openmc.ZCylinder(r=R + t_r), openmc.ZPlane(-H / 2 - t_r), openmc.ZPlane(H / 2 + t_r)
        for s in (c_out, zb, zt):
            s.boundary_type = "vacuum"
        cells.append(openmc.Cell(fill=refl, region=(-c_out & +zb & -zt) & ~core))
    else:
        for s in (c_in, z0, z1):
            s.boundary_type = "vacuum"
    st = openmc.Settings()
    st.particles, st.batches, st.inactive = particles, batches, inactive
    st.source = openmc.IndependentSource(space=openmc.stats.Box((-R / 3, -R / 3, -H / 4), (R / 3, R / 3, H / 4)))
    st.temperature = {"method": "interpolation", "default": fuel.temperature}
    st.output = {"tallies": False, "summary": False}
    model = openmc.Model(openmc.Geometry(cells), openmc.Materials(mats), st)
    model.materials.cross_sections = str(XS)
    with tempfile.TemporaryDirectory() as tmp:
        cwd = os.getcwd(); os.chdir(tmp)
        try:
            sp = model.run(threads=int(os.environ.get("OMP_THREADS", "4")), output=False)
            with openmc.StatePoint(sp) as f:
                return float(f.keff.nominal_value), float(f.keff.std_dev)
        finally:
            os.chdir(cwd)


def void_scan(make, rho0, R, H0, refl=None, t_r=0.0, voids=(0.0, 0.1, 0.2, 0.3)):
    rows = []
    for a in voids:
        k, sd = keff(make(rho0 * (1 - a)), R, H0 / (1 - a), refl, t_r)
        rows.append({"void": a, "k": k, "sd": sd, "rho_pcm": 1e5 * (1 - 1 / k)})
        print(f"   void {a:.2f}: k {k:.4f} +- {sd:.4f}", flush=True)
    for r in rows:
        r["worth_pcm"] = r["rho_pcm"] - rows[0]["rho_pcm"]
    return rows


def main():
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    liq = BM.chloride_fuel(2000.0, 0.30)
    rho_cl = liq.rho / 1000
    # chloride: find a Pu fraction that is about critical for a 1.5 m x 3 m pool with a 30 cm Pb reflector
    pb = N.element_material("Pb", 9.8)
    if "chloride" not in res:
        R, H = 150.0, 300.0
        print("chloride: Pu search, rho", rho_cl, flush=True)
        lo, hi, kl, kh = 0.15, 0.35, None, None
        kl, _ = keff(chloride(lo, rho_cl), R, H, pb, 30.0)
        kh, _ = keff(chloride(hi, rho_cl), R, H, pb, 30.0)
        pu = lo + (1 - kl) * (hi - lo) / (kh - kl)
        pu = min(max(pu, 0.10), 0.45)
        print(f"   k(pu {lo}) {kl:.4f}, k(pu {hi}) {kh:.4f} -> pu {pu:.3f}", flush=True)
        res["chloride"] = {"R_cm": R, "H_cm": H, "reflector": "Pb 30 cm", "rho_gcc": rho_cl, "pu": pu,
                           "k_pu_lo": [lo, kl], "k_pu_hi": [hi, kh],
                           "scan": void_scan(lambda r: chloride(pu, r), rho_cl, R, H, pb, 30.0)}
        OUT.write_text(json.dumps(res, indent=1))
    if "metal" not in res:
        # liquid U-Pu pool at its W-reflected critical size from the geometry study (R 16.0 cm, H/D 1, Pu 15 %)
        W = N.element_material("W", 19.0)
        rho_m = 17.2 - 1.0e-3 * (2000.0 - 1408.0)
        print("metal pool", flush=True)
        res["metal"] = {"R_cm": 16.0, "H_cm": 32.0, "reflector": "W 20 cm", "rho_gcc": rho_m, "pu": 0.15,
                        "scan": void_scan(lambda r: N.fuel_material("UPu_liquid", 0.15, r), rho_m, 16.0, 32.0, W, 20.0)}
        OUT.write_text(json.dumps(res, indent=1))
    if "metal_large" not in res:
        # a large reflected U-Pu pool (1.5 m x 3 m, diluted to ~45 % fuel with W structure as in A2/R-type cores)
        W = N.element_material("W", 19.0)
        rho_m = 17.2 - 1.0e-3 * (2000.0 - 1408.0)
        def diluted(r):
            return openmc.Material.mix_materials([N.fuel_material("UPu_liquid", 0.10, r), N.element_material("W", 19.0)],
                                                 [0.45, 0.10], "vo")
        print("large diluted metal core", flush=True)
        res["metal_large"] = {"R_cm": 150.0, "H_cm": 300.0, "reflector": "W 20 cm", "note": "45 % U-Pu (Pu 10 %), 10 % W, rest void/coolant gas",
                              "scan": void_scan(diluted, rho_m, 150.0, 300.0, W, 20.0)}
        OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

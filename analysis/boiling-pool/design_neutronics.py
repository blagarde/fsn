"""OpenMC check of the reference pin core (design.py): critical Pu fraction and void worth.

Homogenised core: 41.5 % liquid U-Pu, tube walls (W-25Re ~ W + Re, TiB2), Al coolant; cylinder D 3.4 m,
H 1.0 m; 20 cm W reflector radially and axially, then 30 cm depleted-U blanket. Void: fuel density x (1-a),
fuel column (and core height) / (1-a). Writes results/design_neutronics.json.
"""
import json, math, sys
from pathlib import Path
import openmc
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[0] / "core-thermal"))
import neutronics as N  # noqa: E402
import importlib
BN = importlib.import_module("neutronics")
d = json.loads((HERE / "results" / "design.json").read_text())
R, H0 = 100 * d["core_diameter_m"] / 2, 100 * d["core_height_m"]
f_fuel = d["fuel_fraction"]
r_f, r_o, pitch = 2.5, d["pin_outer_radius_mm"] / 10, d["pitch_mm"] / 10
f_metal = math.pi * ((2.5 + 0.15) ** 2 - 2.5 ** 2) / pitch ** 2
f_bar = math.pi * (r_o ** 2 - (2.5 + 0.15) ** 2) / pitch ** 2
f_al = 1 - math.pi * r_o ** 2 / pitch ** 2

def core(pu, a):
    rho_f = (17.2 - 1.0e-3 * (1900 - 1408)) * (1 - a)
    W = BN.element_material("W", 19.3); Re = BN.element_material("Re", 21.0)
    tib2 = openmc.Material(); tib2.add_element("Ti", 1.0) if False else None
    tib2 = openmc.Material(name="TiB2")
    for n, f in BN.M.natural("Ti").items(): tib2.add_nuclide(n, f)
    tib2.add_nuclide("B11", 2 * 0.999); tib2.add_nuclide("B10", 0.0) if False else None
    tib2.set_density("g/cm3", 4.5)
    al = BN.element_material("Al", 2.1)
    fuel = BN.fuel_material("UPu_liquid", pu, rho_f)
    return openmc.Material.mix_materials([fuel, W, Re, tib2, al], [f_fuel, 0.75 * f_metal, 0.25 * f_metal, f_bar, f_al], "vo")

def keff(pu, a=0.0, particles=20000, batches=70, inactive=20):
    import os, tempfile
    m = core(pu, a); m.temperature = 1900.0
    H = H0 / (1 - a)
    W = BN.element_material("W", 19.3); W.temperature = 1500.0
    U = BN.element_material("Udep", 18.9); U.temperature = 1200.0
    c0, z0, z1 = openmc.ZCylinder(r=R), openmc.ZPlane(-H/2), openmc.ZPlane(H/2)
    c1, z2, z3 = openmc.ZCylinder(r=R+20), openmc.ZPlane(-H/2-20), openmc.ZPlane(H/2+20)
    c2, z4, z5 = openmc.ZCylinder(r=R+50, boundary_type="vacuum"), openmc.ZPlane(-H/2-50, boundary_type="vacuum"), openmc.ZPlane(H/2+50, boundary_type="vacuum")
    inner = -c0 & +z0 & -z1; mid = (-c1 & +z2 & -z3) & ~inner; outer = (-c2 & +z4 & -z5) & ~(-c1 & +z2 & -z3)
    geom = openmc.Geometry([openmc.Cell(fill=m, region=inner), openmc.Cell(fill=W, region=mid), openmc.Cell(fill=U, region=outer)])
    st = openmc.Settings(); st.particles, st.batches, st.inactive = particles, batches, inactive
    st.source = openmc.IndependentSource(space=openmc.stats.Box((-R/2, -R/2, -H/4), (R/2, R/2, H/4)))
    st.temperature = {"method": "interpolation", "default": 1900.0}; st.output = {"tallies": False, "summary": False}
    model = openmc.Model(geom, openmc.Materials([m, W, U]), st)
    model.materials.cross_sections = str(HERE.parents[1] / "data" / "openmc" / "cross_sections.xml")
    with tempfile.TemporaryDirectory() as tmp:
        cwd = os.getcwd(); os.chdir(tmp)
        try:
            with openmc.StatePoint(model.run(threads=int(os.environ.get("OMP_THREADS", "4")), output=False)) as f:
                return float(f.keff.nominal_value), float(f.keff.std_dev)
        finally:
            os.chdir(cwd)

res = {}
k1, _s = keff(0.10); k2, _s = keff(0.16)
pu = 0.10 + (1 - k1) * 0.06 / (k2 - k1)
res["pu_search"] = {"pu_0.10": k1, "pu_0.16": k2, "pu_critical_est": pu}
print(res, flush=True)
scan = []
for a in (0.0, 0.05, 0.10, 0.20):
    k, sd = keff(pu, a); scan.append({"void": a, "k": k, "sd": sd, "rho_pcm": 1e5 * (1 - 1 / k)}); print(scan[-1], flush=True)
for s in scan: s["worth_pcm"] = s["rho_pcm"] - scan[0]["rho_pcm"]
res["void_scan"] = scan
(HERE / "results" / "design_neutronics.json").write_text(json.dumps(res, indent=1))

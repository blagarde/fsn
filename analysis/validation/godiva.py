"""Library validation: Godiva (ICSBEP HEU-MET-FAST-001), bare HEU metal sphere, benchmark k_eff = 1.0000.

Atom densities (atoms/barn-cm) and radius are the ICSBEP benchmark model values for case 1 (approx.,
from memory of the published specification; verify against the ICSBEP handbook).
Usage: python analysis/validation/godiva.py [cross_sections.xml]
"""
import glob, json, os, sys, tempfile
from pathlib import Path

import openmc
import openmc.data

ROOT = Path(__file__).resolve().parents[2]
xs = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "data" / "openmc" / "cross_sections.xml")
if not Path(xs).exists():  # library still building: index what exists
    lib = openmc.data.DataLibrary()
    for f in sorted(glob.glob(str(ROOT / "data" / "openmc" / "*.h5"))):
        lib.register_file(f)
    xs = os.path.join(tempfile.mkdtemp(), "cs.xml")
    lib.export_to_xml(xs)

u = openmc.Material(name="HEU")
u.add_nuclide("U234", 4.9184e-4)
u.add_nuclide("U235", 4.4994e-2)
u.add_nuclide("U238", 2.4984e-3)
u.set_density("sum")
u.temperature = 293.6  # library has 1200/2100 K only: nearest temperature is used (Doppler negligible for HEU metal)
sphere = openmc.Sphere(r=8.7407, boundary_type="vacuum")
geom = openmc.Geometry([openmc.Cell(fill=u, region=-sphere)])
s = openmc.Settings()
s.particles, s.batches, s.inactive = 20000, 120, 20
s.source = openmc.IndependentSource(space=openmc.stats.Point())
s.temperature = {"method": "nearest", "tolerance": 2000.0}
mats = openmc.Materials([u]); mats.cross_sections = xs
model = openmc.Model(geom, mats, s)
with tempfile.TemporaryDirectory() as tmp:
    os.chdir(tmp)
    with openmc.StatePoint(model.run(threads=int(os.environ.get("OMP_NUM_THREADS", "1")), output=False)) as sp:
        k = sp.keff
result = {"case": "HEU-MET-FAST-001 (Godiva)", "benchmark_keff": 1.0000, "calc_keff": k.nominal_value,
          "sd": k.std_dev, "diff_pcm": 1e5 * (k.nominal_value - 1.0), "library_T_used_K": 1200}
print(json.dumps(result, indent=1))
(ROOT / "analysis" / "validation" / "godiva_result.json").write_text(json.dumps(result, indent=1))

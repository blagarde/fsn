"""One-group neutron constants for the core nuclear-thermal model, collapsed with OpenMC.

The core model (neutronics.py) uses one-group diffusion so that it can sweep thousands of
compositions in seconds. Its constants come from here: an OpenMC run of an infinite homogeneous
reference mixture, with every nuclide of the transport library present (the ones not in the
reference recipe at a trace density, so they see the reference spectrum without changing it).
Per nuclide, track-length tallies give the flux-weighted one-group
  total, scatter P0 and P1 (for the transport correction), absorption, fission, nu-fission,
  (n,gamma), (n,2n), delayed-nu-fission and decay rate by delayed group (6 groups, ENDF/B-VIII.0)
and, for the mixture, 1/v (for the prompt neutron generation time).

Three reference spectra (hard, medium, soft) x two library temperatures (1200, 2100 K); the
temperature pair gives the Doppler effect. A composition's spectrum is matched to the nearest
reference by its median flux energy (neutronics.py), which is the main approximation of the model.

Run (takes 1-2 h on 4 busy cores):  /opt/mamba/envs/nuc/bin/python constants.py [--particles N]
Writes results/constants.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import openmc

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
import importlib.util as _ilu  # load new-geometries/materials.py by path (its folder also has a thermal.py)
_spec = _ilu.spec_from_file_location("ng_materials", ROOT / "analysis" / "new-geometries" / "materials.py")
M = _ilu.module_from_spec(_spec)
sys.modules["ng_materials"] = M
_spec.loader.exec_module(M)  # shared Pu vector, U vector, natural abundances, densities
import p1data  # noqa: E402

XS = ROOT / "data" / "openmc" / "cross_sections.xml"
OUT = Path(os.environ.get("CORE_CONSTANTS", HERE / "results" / "constants.json"))
TEMPS = (1200.0, 2100.0)
TRACE = 1e-9  # atom fraction of a trace nuclide relative to the mixture
PU_REF = 0.15
# Fine groups for the Doppler-consistent collapse (neutronics.py collapses both temperatures with one
# spectrum, so run-to-run spectrum noise cannot masquerade as a temperature effect)
G_EDGES = np.concatenate([[1e-5, 1.0], np.logspace(0, np.log10(2e7), 81)[1:]])
G_SCORES = ["total", "absorption", "fission", "nu-fission", "(n,gamma)", "(n,2n)"]


def mox(pu: float) -> openmc.Material:
    m = openmc.Material(name="(U,Pu)O2")
    M.heavy_metal(m, pu)
    m.add_nuclide("O16", 2.0)
    m.set_density("g/cm3", 10.4)  # ~95 % of theoretical (approx.)
    return m


def steel() -> openmc.Material:
    m = openmc.Material(name="steel (Fe-17Cr-12Ni, approx.)")
    for el, w in (("Fe", 0.71), ("Cr", 0.17), ("Ni", 0.12)):
        for nuc, f in M.natural(el).items():
            m.add_nuclide(nuc, w * f, "wo")
    m.set_density("g/cm3", 7.6)
    return m


def sodium() -> openmc.Material:
    m = openmc.Material(name="Na liquid")
    m.add_nuclide("Na23", 1.0)
    m.set_density("g/cm3", 0.78)  # ~800 K (approx.)
    return m


def metal_solid(pu: float) -> openmc.Material:
    m = openmc.Material(name="U-Pu metal")
    M.heavy_metal(m, pu)
    m.set_density("g/cm3", 16.0)
    return m


# Reference recipes, volume fractions. Median flux energies come out roughly hard > medium > soft.
REFERENCES = {
    "hard":   lambda: [(metal_solid(PU_REF), 0.50), (M.Pb(), 0.35), (M.W(), 0.15)],
    "medium": lambda: [(M.upun(PU_REF), 0.40), (M.Al(), 0.40), (M.W(), 0.20)],
    "soft":   lambda: [(mox(PU_REF), 0.35), (sodium(), 0.40), (steel(), 0.25)],
}


def library_nuclides() -> list[str]:
    lib = openmc.data.DataLibrary.from_xml(str(XS))
    return sorted(e["materials"][0] for e in lib.libraries if e["type"] == "neutron")


def run(ref: str, T: float, particles: int, batches: int, inactive: int) -> dict:
    comps = REFERENCES[ref]()
    mix = openmc.Material.mix_materials([m for m, _ in comps], [f for _, f in comps], "vo")
    dens = mix.get_nuclide_atom_densities()  # atom/b-cm
    total = sum(dens.values())
    m = openmc.Material(name=f"{ref} {T:.0f} K", temperature=T)
    for nuc in library_nuclides():
        m.add_nuclide(nuc, dens.get(nuc, TRACE * total))
    m.set_density("atom/b-cm", total * (1 + TRACE * (len(library_nuclides()) - len(dens))))
    nuclides = library_nuclides()

    box = openmc.model.RectangularParallelepiped(-1, 1, -1, 1, -1, 1, boundary_type="reflective")
    cell = openmc.Cell(fill=m, region=-box)
    geom = openmc.Geometry([cell])
    s = openmc.Settings()
    s.particles, s.batches, s.inactive = particles, batches, inactive
    s.source = openmc.IndependentSource(space=openmc.stats.Box((-1, -1, -1), (1, 1, 1)))
    s.temperature = {"method": "interpolation", "default": T}
    s.output = {"tallies": False, "summary": False}

    t_n = openmc.Tally(name="nuc")
    t_n.nuclides = nuclides
    t_n.scores = ["total", "absorption", "fission", "nu-fission", "(n,gamma)", "(n,2n)"]
    t_g = openmc.Tally(name="nucg")
    t_g.nuclides = nuclides
    t_g.filters = [openmc.EnergyFilter(G_EDGES)]
    t_g.scores = G_SCORES
    t_gf = openmc.Tally(name="fluxg")
    t_gf.filters = [openmc.EnergyFilter(G_EDGES)]
    t_gf.scores = ["flux"]
    t_s = openmc.Tally(name="scatter")
    t_s.nuclides = nuclides
    t_s.filters = [openmc.LegendreFilter(1)]
    t_s.scores = ["scatter"]
    t_d = openmc.Tally(name="delayed")
    t_d.nuclides = nuclides
    t_d.filters = [openmc.DelayedGroupFilter(list(range(1, 7)))]
    t_d.scores = ["delayed-nu-fission", "decay-rate"]
    t_m = openmc.Tally(name="mix")
    t_m.scores = ["flux", "inverse-velocity", "nu-fission", "absorption"]
    edges = np.logspace(-5, np.log10(2e7), 301)
    t_e = openmc.Tally(name="spectrum")
    t_e.filters = [openmc.EnergyFilter(edges)]
    t_e.scores = ["flux"]

    model = openmc.Model(geom, openmc.Materials([m]), s, tallies=openmc.Tallies([t_n, t_g, t_gf, t_s, t_d, t_m, t_e]))
    model.materials.cross_sections = str(XS)
    with tempfile.TemporaryDirectory() as tmp:
        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            sp_path = model.run(threads=int(os.environ.get("OMP_THREADS", "2")), output=False)
            with openmc.StatePoint(sp_path) as sp:
                k = sp.keff
                tn, ts, td = sp.get_tally(name="nuc"), sp.get_tally(name="scatter"), sp.get_tally(name="delayed")
                tm, te = sp.get_tally(name="mix"), sp.get_tally(name="spectrum")
                flux_mix = float(tm.get_values(scores=["flux"]).ravel()[0])
                inv_v = float(tm.get_values(scores=["inverse-velocity"]).ravel()[0]) / flux_mix
                spec = te.mean.ravel()
                tg = sp.get_tally(name="nucg")
                flux_g = sp.get_tally(name="fluxg").mean.ravel()
                per = {}
                for nuc in nuclides:
                    n_at = m.get_nuclide_atom_densities()[nuc]  # atom/b-cm -> sigma in barns
                    def g(score, tally=tn, **kw):
                        return float(tally.get_values(nuclides=[nuc], scores=[score], **kw).ravel()[0])
                    phi = flux_mix
                    sig = lambda score: g(score) / (phi * n_at)
                    s0 = float(ts.get_values(nuclides=[nuc], scores=["scatter"], filters=[openmc.LegendreFilter], filter_bins=[("P0",)]).ravel()[0])
                    s1 = float(ts.get_values(nuclides=[nuc], scores=["scatter"], filters=[openmc.LegendreFilter], filter_bins=[("P1",)]).ravel()[0])
                    dnf = [float(td.get_values(nuclides=[nuc], scores=["delayed-nu-fission"], filters=[openmc.DelayedGroupFilter], filter_bins=[(i,)]).ravel()[0]) for i in range(1, 7)]
                    dr = [float(td.get_values(nuclides=[nuc], scores=["decay-rate"], filters=[openmc.DelayedGroupFilter], filter_bins=[(i,)]).ravel()[0]) for i in range(1, 7)]
                    nuf = g("nu-fission")
                    present = nuc in dens
                    el, el_p1 = p1data.sigma_s1(nuc, f"{T:.0f}K", edges, spec)
                    per[nuc] = {
                        "present": present,
                        # analog scatter tallies are empty for trace nuclides: use total - absorption and the
                        # data-derived elastic P1 for those (p1data.py); present nuclides keep both for checking
                        "total": sig("total"),
                        "scatter": s0 / (phi * n_at) if present else sig("total") - sig("absorption"),
                        "scatter_p1_analog": s1 / (phi * n_at) if present else None,
                        "elastic_data": el, "scatter_p1_data": el_p1,
                        "absorption": sig("absorption"), "fission": sig("fission"), "nu_fission": sig("nu-fission"),
                        "capture": sig("(n,gamma)"), "n2n": sig("(n,2n)"),
                        # beta_i = delayed nu-fission / nu-fission; lambda_i = decay-rate / delayed nu-fission
                        "beta": [d / nuf if nuf > 0 else 0.0 for d in dnf],
                        "lambda": [r / d if d > 0 else 0.0 for r, d in zip(dr, dnf)],
                        "groups": {sc: [float(x) for x in np.divide(tg.get_values(nuclides=[nuc], scores=[sc]).ravel(),
                                                                     flux_g * n_at, out=np.zeros_like(flux_g), where=flux_g > 0)]
                                   for sc in G_SCORES},
                    }
        finally:
            os.chdir(cwd)
    cdf = np.cumsum(spec) / spec.sum()
    return {"reference": ref, "T_K": T, "k_inf": float(k.nominal_value), "k_inf_sd": float(k.std_dev),
            "median_energy_eV": float(edges[1:][np.searchsorted(cdf, 0.5)]),
            "inverse_velocity_s_per_cm": inv_v,
            "group_edges_eV": G_EDGES.tolist(), "flux_g": flux_g.tolist(),
            "recipe": [(mm.name, f) for mm, f in comps], "pu_frac": PU_REF, "sigma_b": per}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--particles", type=int, default=10000)
    ap.add_argument("--batches", type=int, default=40)
    ap.add_argument("--inactive", type=int, default=15)
    ap.add_argument("--only", nargs="*", default=None, help="e.g. hard:1200")
    a = ap.parse_args()
    OUT.parent.mkdir(exist_ok=True)
    data = json.loads(OUT.read_text()) if OUT.exists() else {}
    for ref in REFERENCES:
        for T in TEMPS:
            key = f"{ref}:{T:.0f}"
            if (a.only and key not in a.only) or (not a.only and key in data):
                continue
            print("running", key, flush=True)
            data[key] = run(ref, T, a.particles, a.batches, a.inactive)
            print(f"  k_inf {data[key]['k_inf']:.4f}  median E {data[key]['median_energy_eV']:.3g} eV", flush=True)
            OUT.write_text(json.dumps(data, indent=1))
    data["_meta"] = {"library": "ENDF/B-VIII.0 via NJOY2016 (tools/openmc_library)", "temperatures_K": TEMPS,
                     "pu_vector": M.PU_VECTOR, "u_vector": M.U_VECTOR, "library_notes": sorted(M.LIBRARY_NOTES)}
    OUT.write_text(json.dumps(data, indent=1))


if __name__ == "__main__":
    main()

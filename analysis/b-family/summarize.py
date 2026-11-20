"""Collect neutronics, thermal and cycle results into results/summary.json and results/summary.csv,
adding inventory indicators (HM and Pu per MWth) and W -> Re transmutation rate for B5."""
from __future__ import annotations

import csv
import json

import openmc

from bfam import HERE
from designs import DESIGNS

R = HERE / "results"
th = json.loads((R / "thermal.json").read_text())
cy = json.loads((R / "cycle.json").read_text())
HM = ("U234", "U235", "U238", "Pu238", "Pu239", "Pu240", "Pu241", "Pu242")
MEV_J = 1.602176634e-13
E_FISS = 200.0 * MEV_J  # J per fission (approx.)

# core power density (MW/m3, core average) and total fuel-bearing volume per MWth, from thermal.json
core_q = {"B1": th["B1"]["core_power_density_MW_m3"], "B2": th["B2"]["core_power_density_MW_m3"],
          "B3": th["B3"]["core_power_density_MW_m3"], "B4": th["B4"]["P_MWth"] / (th["B4"]["V_core_m3"] + th["B4"]["V_loop_m3"]),
          "B5": th["B5"]["core_power_density_MW_m3"], "B6": th["B6"]["core_power_density_MW_m3"]}
design_of = lambda case: case.split("-")[0]
rows, full = [], {}
for case in DESIGNS:
    f = R / f"neutronics_{case}.json"
    if not f.exists():
        continue
    n = json.loads(f.read_text())
    x = n["pu_frac_at_k1.15"]
    d = design_of(case)
    mix = openmc.Material.mix_materials([m for m, _ in DESIGNS[case]["build"](x)],
                                        [v for _, v in DESIGNS[case]["build"](x)], "vo")
    hm_density = sum(mix.get_mass_density(nuc) for nuc in HM if nuc in mix.get_nuclides())  # g/cm3 homogenised
    pu_density = sum(mix.get_mass_density(nuc) for nuc in HM if nuc.startswith("Pu") and nuc in mix.get_nuclides())
    q = core_q[d]  # MW/m3 (for B4: per m3 of total salt inventory)
    hm_t_per_MW = hm_density * 1e6 / 1e6 / q  # g/cm3 -> t/m3 ; / (MW/m3) -> t/MW
    a = n["at_target"]
    row = {"case": case, "T_K": n["T_rep_K"], "pu_frac": x, "k_inf": a["k_inf"], "k_sd": a["k_inf_sd"],
           "CR": a["conversion_ratio"], "median_E_keV": a["median_energy_eV"] / 1e3,
           "flux_below_1keV": a["flux_fraction"]["<1keV"], "parasitic_share": a["parasitic_total_share"],
           "top_absorbers": "; ".join(f"{k} {100*v:.1f}%" for k, v in list(a["parasitic_absorption_share"].items())[:4]),
           "void_pcm": n.get("void", {}).get("worth_pcm"), "void_sd": n.get("void", {}).get("worth_sd_pcm"),
           "dT_1200_2100_pcm": n["temperature"]["dk_pcm_1200_to_2100"], "dT_sd": n["temperature"]["sd_pcm"],
           "doppler_const_pcm": n["temperature"]["doppler_constant_pcm"],
           "tritium_per_fission": a["tritium_per_fission"],
           "HM_t_per_MWth": hm_t_per_MW, "Pu_kg_per_MWth": pu_density * 1e3 / q,
           "specific_power_MW_per_tHM": 1 / hm_t_per_MW,
           "T_out_C": cy[d]["T_out_C"], "carnot": cy[d]["carnot"], "curzon_ahlborn": cy[d]["curzon_ahlborn"],
           "brayton_net": cy[d]["brayton_He"]["eta_net"]}
    # W -> Re (and Mo -> Tc/Ru) transmutation: captures per fission x fission rate / matrix atoms
    if case.startswith("B5"):
        mat_nucs = [k for k in a["capture_per_fission"] if k.startswith("W") or k.startswith("Mo")]
        cap = sum(a["capture_per_fission"][k] for k in mat_nucs)
        dens = mix.get_nuclide_atom_densities()  # atoms/b-cm
        n_mat = sum(v for k, v in dens.items() if k.startswith("W") or k.startswith("Mo")) * 1e24  # /cm3
        fiss_rate = q * 1e6 / E_FISS / 1e6  # fissions /cm3/s (q in MW/m3 -> W/cm3 = q)
        row["matrix_capture_at_pct_per_year"] = 100 * cap * fiss_rate * 3.156e7 / n_mat
    for vname, v in n.get("variants", {}).items():
        row[f"variant: {vname}"] = f"k {v['k_inf']:.4f} ({v['dk_pcm']:+.0f} pcm), CR {v['CR']:.3f}"
    rows.append(row)
    full[case] = row
(R / "summary.json").write_text(json.dumps(full, indent=1))
keys = sorted({k for r in rows for k in r}, key=lambda k: list(rows[0].keys()).index(k) if k in rows[0] else 999)
with open(R / "summary.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=keys)
    w.writeheader()
    w.writerows(rows)
for r in rows:
    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})

"""Derive worths and tables from results/neutronics_cases.json -> results/summary.json and summary.md."""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE / "results"


def rho(k):
    return (k - 1) / k


def worth(db, ref, pert):
    a, b = db[ref], db[pert]
    w = 1e5 * (rho(b["k_inf"]) - rho(a["k_inf"]))
    sd = 1e5 * math.hypot(a["k_inf_sd"] / a["k_inf"] ** 2, b["k_inf_sd"] / b["k_inf"] ** 2)
    return {"pcm": w, "sd_pcm": sd, "dCR": b["conversion_ratio"] - a["conversion_ratio"],
            "k_ref": a["k_inf"], "k_pert": b["k_inf"], "CR_pert": b["conversion_ratio"],
            "E50_keV_pert": b["median_energy_eV"] / 1e3}


def main():
    db = json.loads((RES / "neutronics_cases.json").read_text())
    crit = json.loads((RES / "critical_pu.json").read_text())
    out = {"critical": crit, "designs": {}}
    pairs = {
        "A1": {"void (Al -> 0)": "A1_void", "T 1600 -> 1200 K": "A1_T1200", "T 1600 -> 2100 K": "A1_T2100",
               "ZrB2 natural B": "A1_Bnat", "ZrB2 99.5% B-11": "A1_B995", "fuel natural N": "A1_Nnat_fuel",
               "W/AlN clad instead of ZrB2": "A1_WAlN", "Na instead of Al": "A1_Na", "Pb instead of Al": "A1_Pb"},
        "A2": {"void (Al -> 0)": "A2_void", "T 2100 -> 1200 K": "A2_T1200", "AlN natural N": "A2_AlN_Nnat",
               "ZrB2 wall (B-11) instead of W/AlN": "A2_ZrB2", "ZrB2 wall natural B": "A2_ZrB2_Bnat",
               "Na instead of Al": "A2_Na", "Pb instead of Al": "A2_Pb"},
        "A3x33": {"T 2100 -> 1200 K": "A3x33_T1200", "10% ZrB2 structure in core": "A3x33_ZrB2_10pct"},
        "A3x20": {"T 2100 -> 1200 K": "A3x20_T1200"},
    }
    second = {  # void worth of variants, relative to their own nominal
        "A1": {"W/AlN void": ("A1_WAlN", "A1_WAlN_void"), "W/AlN AlN natural N": ("A1_WAlN", "A1_WAlN_Nnat"),
               "Na void": ("A1_Na", "A1_Na_void"), "Pb void": ("A1_Pb", "A1_Pb_void")},
        "A2": {"ZrB2 wall void": ("A2_ZrB2", "A2_ZrB2_void"), "Na void": ("A2_Na", "A2_Na_void"),
               "Pb void": ("A2_Pb", "A2_Pb_void"), "ZrB2 natural B vs B-11": ("A2_ZrB2", "A2_ZrB2_Bnat")},
    }
    md = []
    for d, items in pairs.items():
        ref = f"{d}_ref"
        if ref not in db:
            continue
        r = db[ref]
        c = crit[d]
        entry = {"pu": c["pu"], "pu_exact": c["pu_exact"], "dk_dpu": c["dk_dpu"], "k_inf": r["k_inf"],
                 "k_sd": r["k_inf_sd"], "CR": r["conversion_ratio"], "E50_keV": r["median_energy_eV"] / 1e3,
                 "parasitic": r["parasitic_absorption_share"], "worths": {}}
        for lab, case in {**items}.items():
            if case in db:
                w = worth(db, ref, case)
                if c["dk_dpu"] and math.isfinite(c["dk_dpu"]):
                    w["pu_shift_equiv"] = -(w["k_pert"] - w["k_ref"]) / c["dk_dpu"]
                entry["worths"][lab] = w
        for lab, (a, b) in second.get(d, {}).items():
            if a in db and b in db:
                entry["worths"][lab] = worth(db, a, b)
        out["designs"][d] = entry
        md.append(f"## {d}\n")
        md.append(f"Pu/(U+Pu) for k_inf 1.15: {c['pu_exact']:.4f} (run at {c['pu']:.4f}; dk/dPu = {c['dk_dpu']:.2f}); "
                  f"k_inf = {r['k_inf']:.4f} +- {r['k_inf_sd']:.4f}; CR = {r['conversion_ratio']:.3f}; "
                  f"median flux energy {r['median_energy_eV']/1e3:.0f} keV\n")
        md.append("Parasitic absorption shares (of all absorption): " +
                  ", ".join(f"{n} {v*100:.2f}%" for n, v in r["parasitic_absorption_share"].items()) + "\n")
        md.append("| Perturbation | Worth (pcm) | sd | dCR | Pu-fraction equivalent |\n| --- | --- | --- | --- | --- |")
        for lab, w in entry["worths"].items():
            pe = w.get("pu_shift_equiv")
            md.append(f"| {lab} | {w['pcm']:+.0f} | {w['sd_pcm']:.0f} | {w['dCR']:+.3f} | "
                      f"{'' if pe is None else f'{pe*100:+.2f} pts'} |")
        md.append("")
    md.append("## B-10 first-order estimates (not transport results)\n")
    md.append("| Case | B-10 fraction of boron | spectrum-avg sigma_abs B-10 (b) | dA/A | drho (pcm) | k_inf transport (B-11 only) | k_inf corrected |")
    md.append("| --- | --- | --- | --- | --- | --- | --- |")
    b10 = {}
    for k, r in sorted(db.items()):
        if "b10" in r:
            b = r["b10"]
            b10[k] = b
            md.append(f"| {k} | {b['b10_fraction']:.4f} | {b.get('sigma_abs_B10_spectrum_avg_b', float('nan')):.2f} | "
                      f"{b.get('dA_over_A', 0):.4f} | {b['drho_pcm']:+.0f} | {r['k_inf_transport_B11only']:.4f} | {r['k_inf']:.4f} |")
    out["b10"] = b10
    md.append("")
    # one-group leakage estimate of the density (expansion) coefficient of a homogeneous liquid core at
    # k_eff = 1: d ln k / d ln rho = 2 (1 - k_eff / k_inf), M^2 ~ rho^-2 (calc, approx.)
    out["density_coefficient_one_group"] = {"k_inf": 1.15, "dlnk_dlnrho": 2 * (1 - 1 / 1.15),
                                            "pcm_per_pct_density": 1e3 * 2 * (1 - 1 / 1.15)}
    md.append("## Scans\n")
    for d, c in crit.items():
        md.append(f"- {d}: " + "; ".join(f"Pu {p:.3f}: k {k:.4f}" for p, k in c["scan"]) +
                  (" (target extrapolated)" if c["extrapolated"] else ""))
    (RES / "summary.json").write_text(json.dumps(out, indent=1))
    (RES / "summary.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()

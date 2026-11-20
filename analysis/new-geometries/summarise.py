"""Merge thermal, neutronics and finite-core results into one row per candidate.

Pu inventory = core fuel mass x heavy-metal fraction x Pu/(U+Pu) at k_inf = 1.15 (core only; no blanket,
no out-of-core inventory). That Pu fraction is an infinite-medium value; finite.py gives the clean-critical
value with leakage for A2 and L7.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).parent / "results"
th = json.loads((HERE / "thermal.json").read_text())
nu = json.loads((HERE / "neutronics.json").read_text())
fi = json.loads((HERE / "finite.json").read_text()) if (HERE / "finite.json").exists() else {}

def refit(n):
    """Pu and CR at k_inf = 1.15 from the best final run and a partner >= 0.015 away in Pu (as neutronics.py)."""
    runs = n.get("runs", [])
    fins = [r for r in runs if r["stats"]["particles"] == 20000]
    if not fins:
        return n
    fin = min(fins, key=lambda r: abs(r["k_inf"] - 1.15))
    far = [r for r in runs if r is not fin and abs(r["pu_frac"] - fin["pu_frac"]) >= 0.015] or [r for r in runs if r is not fin]
    o = min(far, key=lambda r: abs(r["k_inf"] - 1.15))
    sl = (fin["k_inf"] - o["k_inf"]) / (fin["pu_frac"] - o["pu_frac"])
    pu = fin["pu_frac"] + (1.15 - fin["k_inf"]) / sl
    cs = (fin["conversion_ratio"] - o["conversion_ratio"]) / (fin["pu_frac"] - o["pu_frac"])
    n = dict(n)
    n["pu_at_1.15"], n["cr_at_1.15"] = pu, fin["conversion_ratio"] + cs * (pu - fin["pu_frac"])
    return n


nu = {k: (refit(v) if isinstance(v, dict) and "runs" in v else v) for k, v in nu.items()}

HM_FRAC = {"UPu": 1.0, "UN": 238.0 / 252.0}   # heavy-metal mass fraction (approx.)


def pick_l7_tube(r=10.0, Th=2000, e=0.8):
    return next(t for t in th["L7"]["tube_sweep"] if t["r_i_mm"] == r and t["Th_C"] == Th and t["eps_container"] == e)


def pick_slab(t, Th=2000, Tout=1500, e=0.8):
    return next(s for s in th["L7"]["slab_sweep"] if s["t_fuel_mm"] == t and s["Th_C"] == Th and s["Tout_C"] == Tout
                and s["eps_container"] == e)


rows = []
def add(cand, case, limit, volume, fuel_t, fuel_kind, outlet, note=""):
    n = nu.get(case, {})
    pu = n.get("pu_at_1.15")
    row = {"candidate": cand, "case": case, "governing_limit": limit, "core_volume_m3": volume,
           "fuel_mass_t": fuel_t, "coolant_outlet_C": outlet,
           "pu_at_kinf_1.15": pu, "cr_at_1.15": n.get("cr_at_1.15"),
           "median_energy_keV": n.get("final", {}).get("median_energy_eV", 0) / 1e3 if n else None,
           "void_worth_pcm": n.get("void", {}).get("worth_pcm"), "void_sd_pcm": n.get("void", {}).get("worth_sd_pcm"),
           "pu_inventory_core_t": (fuel_t * HM_FRAC[fuel_kind] * pu) if (pu and fuel_t) else None, "note": note}
    if case in fi:
        row.update({"finite_pu_critical": fi[case].get("pu_critical"), "finite_BR": fi[case].get("BR_at_critical")})
    rows.append(row)


add("A2 (reference)", "A2_ref", "tube-wall flux 3 MW/m2 (A2 page)", 3.3, 35.0, "UPu", "1,750-1,880")
t = pick_l7_tube()
add("L7 tubes, Al/AlN panels", "L7_tube_Al", f"radiation {t['q_tube_surface_avg_MW_m2']:.2f} MW/m2 (coated W, 2,000 C)",
    t["core_volume_m3"], t["fuel_mass_t"], "UPu", "1,500")
add("L7 tubes, Pb/Mo panels", "L7_tube_Pb", "as above; Pb outlet <= ~1,450 C at 1 bar", t["core_volume_m3"], t["fuel_mass_t"], "UPu", "1,400-1,500")
add("L7 tubes, He/Mo panels", "L7_tube_He", "as above, ~12% less flux (He film)", t["core_volume_m3"] / 0.88, t["fuel_mass_t"] / 0.88, "UPu", "1,300-1,500")
s20 = pick_slab(20)
add("L7 plates 20 mm", "L7_plate20_Al", f"radiation {s20['q_avg_MW_m2']:.2f} MW/m2", s20["core_volume_m3"], s20["fuel_mass_t"], "UPu", "1,500")
s40 = pick_slab(40)
add("L7 plates 40 mm", "L7_plate40_Al", f"radiation {s40['q_avg_MW_m2']:.2f} MW/m2", s40["core_volume_m3"], s40["fuel_mass_t"], "UPu", "1,500")
z = th["S9"]["eps0.8_Th2000_Tout1500_zoned"]
add("S9 radiating UN plates", "S9_UN_Al", f"radiation {z['q_avg_MW_m2']:.2f} MW/m2 (zoned power)", z["core_volume_m3"], z["fuel_mass_t"], "UN", "1,500")
b = th["S5"]["He7MPa_d1.0mm_4umf"]
add("S5 fluidised bed, He", "S5_bed_He", f"fluidisation window: {b['q_per_bed_area_MW_m2']:.0f} MW per m2 of bed", b["bed_area_for_1GW_m2"] * 1.0,
    b["bed_area_for_1GW_m2"] * 1.0 * 0.43 * 13.6, "UN", "1,200", "bed 1 m tall assumed")
s6 = th["S6"]
add("S6 printed lattice, He", "S6_lattice_He", f"He pumping {s6['pumping_MW']:.0f} MW at 100 MW/m3", s6["core_volume_m3"], s6["core_volume_m3"] * 0.42 * 13.6, "UN", "1,100-1,300")
s8 = th["S8"]["h600"]
add("S8 particle-cooled pins", "S8_particles", f"granular h ~600 W/m2K: {s8['q_MW_m2']:.2f} MW/m2", s8["core_volume_m3"],
    s8["core_volume_m3"] * th["S8"]["fractions"]["fuel"] * 13.6, "UN", "~1,200")
l3 = th["L3"]
add("L3 liquid-fuel pins, Al", "L3_pins_Al", "wall flux 3 MW/m2 (as A2)", l3["core_volume_m3_q3"], l3["fuel_mass_t_q3"], "UPu", "1,750-1,900", "core size then set by criticality, not heat")
add("L3 liquid-fuel pins, Pb", "L3_pins_Pb", "wall flux 3 MW/m2; Pb 3.3 bar for 1,700 C", l3["core_volume_m3_q3"], l3["fuel_mass_t_q3"] * 0.5212 / 0.4668, "UPu", "1,450-1,700")
f = th["L5"]["film_2.0mm"]
add("L5 falling film, Al", "L5_film_Al", "wall flux 3 MW/m2 (as A2)", f["core_volume_m3_at_3MW_m2"], f["fuel_in_core_t"], "UPu", "1,750-1,900", "film moves ~1 m/s")

with open(HERE / "summary.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=sorted({k for r in rows for k in r}, key=lambda k: list(rows[0]).index(k) if k in rows[0] else 99))
    w.writeheader(); w.writerows(rows)
(HERE / "summary.json").write_text(json.dumps(rows, indent=1))
for r in rows:
    print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})

"""Family X: infinite-medium neutronics screen (analysis/common/infinite.py) at 2,100 K.

Cases
  fuel   : liquid U-Pu metal alone, k_inf vs Pu/(U+Pu)
  X1     : fuel + Pb (in tubes) + W tube wall, volume fractions from thermal.py reference geometry;
           Pb and W fraction sweeps; Pb void; Doppler 1,200 vs 2,100 K; W-186-enriched wall
  X2     : fuel + CaF2 holdup sweep; Pu sweep at reference holdup; salt removal; Doppler; Ca-44 bounding case
  X3     : fuel + liquid Ca fraction sweep (+ vapour); Ca liquid -> vapour worth; Doppler
Each run is cached in results/runs/<label>.json (delete to rerun). Summary: results/neutronics.json.

Run: export PATH=/opt/mamba/envs/nuc/bin:$PATH; python analysis/x-family/neutronics.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import openmc

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "analysis" / "common"))
from infinite import screen  # noqa: E402

RUNS = HERE / "results" / "runs"
RUNS.mkdir(parents=True, exist_ok=True)
T = 2100.0
KW = dict(particles=20000, batches=60, inactive=20, threads=1)
K_TARGET = 1.15

# ----------------------------------------------------------------- assumptions (approx.)
RHO = {"fuel": 16.4,      # liquid U-Pu at ~2,000 C (approx.; liquid U ~17.3 at its melting point, ~ -1e-3 g/cm3/K)
       "Pb": 8.7,         # liquid Pb at ~2,000 C (approx.)
       "W": 19.0,         # W at ~2,000 C (approx.)
       "CaF2": 2.4,       # liquid CaF2 at ~2,000 C (approx.)
       "Ca_l": 1.2,       # liquid Ca at ~2,000 C (approx.)
       "Ca_v": 1.95e-3}   # Ca vapour at 9.2 bar, 2,000 C, ideal gas (calc from db vapour pressure)
PU_VECTOR = {"Pu238": 0.02, "Pu239": 0.60, "Pu240": 0.24, "Pu241": 0.09, "Pu242": 0.05}  # reactor-grade (approx.)
U_VECTOR = {"U235": 0.0025, "U238": 0.9975}  # depleted uranium


def fuel(x_pu: float) -> openmc.Material:
    m = openmc.Material(name=f"UPu x={x_pu:.3f}")
    for n, a in U_VECTOR.items():
        m.add_nuclide(n, (1 - x_pu) * a, "ao")
    for n, a in PU_VECTOR.items():
        m.add_nuclide(n, x_pu * a, "ao")
    m.set_density("g/cm3", RHO["fuel"])
    return m


def lead():
    m = openmc.Material(name="Pb")
    m.add_element("Pb", 1.0)
    m.set_density("g/cm3", RHO["Pb"])
    return m


def tungsten(w186: float | None = None):
    m = openmc.Material(name="W")
    if w186 is None:
        m.add_element("W", 1.0)
    else:  # enriched W-186, remainder W-184
        m.add_nuclide("W186", w186)
        m.add_nuclide("W184", 1 - w186)
    m.set_density("g/cm3", RHO["W"])
    return m


def caf2(ca44: bool = False):
    m = openmc.Material(name="CaF2")
    if ca44:
        m.add_nuclide("Ca44", 0.99 / 3)
        m.add_nuclide("Ca40", 0.01 / 3)
    else:
        m.add_element("Ca", 1 / 3)
    m.add_nuclide("F19", 2 / 3)
    m.set_density("g/cm3", RHO["CaF2"])
    return m


def calcium(rho: float, name: str):
    m = openmc.Material(name=name)
    m.add_element("Ca", 1.0)
    m.set_density("g/cm3", rho)
    return m


def void():
    m = openmc.Material(name="void-filler")
    m.add_nuclide("He4", 1.0)
    m.set_density("g/cm3", 1e-9)
    return m


def run(label: str, comps, temp: float = T) -> dict:
    f = RUNS / f"{label}.json"
    if f.exists():
        return json.loads(f.read_text())
    t0 = time.time()
    r = screen(comps, temp, label=label, **KW)
    r["fractions"] = {m.name: fr for m, fr in comps}
    r["wall_s"] = round(time.time() - t0, 1)
    f.write_text(json.dumps(r, indent=1))
    print(f"  {label}: k={r['k_inf']:.4f}+-{r['k_inf_sd']:.4f} CR={r['conversion_ratio']:.3f} "
          f"Emed={r['median_energy_eV']/1e3:.0f} keV ({r['wall_s']} s)", flush=True)
    return r


def rho_pcm(k):
    return 1e5 * (k - 1) / k


def worth(a, b):
    """Reactivity of b relative to a, pcm, with 1-sigma."""
    w = rho_pcm(b["k_inf"]) - rho_pcm(a["k_inf"])
    sd = 1e5 * np.hypot(a["k_inf_sd"] / a["k_inf"] ** 2, b["k_inf_sd"] / b["k_inf"] ** 2)
    return {"pcm": round(w, 0), "sd_pcm": round(float(sd), 0)}


def solve_x(points):
    """Pu fraction where k_inf = K_TARGET, from a linear fit k(x) over the given (x, run) points."""
    xs = np.array([x for x, _ in points]); ks = np.array([r["k_inf"] for _, r in points])
    a, b = np.polyfit(xs, ks, 1)
    x_star = (K_TARGET - b) / a
    crs = np.array([r["conversion_ratio"] for _, r in points])
    ca, cb = np.polyfit(xs, crs, 1)
    return {"x_pu": round(float(x_star), 4), "dk_dx": round(float(a), 3),
            "cr_at_x": round(float(ca * x_star + cb), 3),
            "points": [{"x": x, "k": r["k_inf"], "sd": r["k_inf_sd"], "cr": r["conversion_ratio"]} for x, r in points]}


def summary(r):
    return {k: r[k] for k in ("label", "T_K", "k_inf", "k_inf_sd", "conversion_ratio", "median_energy_eV",
                              "parasitic_absorption_share", "fractions", "temperature_note")}


def main():
    thermal = json.loads((HERE / "results" / "thermal.json").read_text())
    x1ref = thermal["X1"]["reference"]
    out = {"T_K": T, "settings": KW, "densities_g_cm3": RHO, "pu_vector_atom": PU_VECTOR, "u_vector_atom": U_VECTOR,
           "k_target": K_TARGET}

    # ---------------- fuel alone
    print("fuel alone")
    pts = [(x, run(f"fuel_x{x:.2f}", [(fuel(x), 1.0)])) for x in (0.08, 0.10, 0.12, 0.15)]
    out["fuel_only"] = solve_x(pts)
    xf = out["fuel_only"]["x_pu"]
    out["fuel_only"]["at_x"] = summary(run("fuel_at_xstar", [(fuel(xf), 1.0)]))
    out["fuel_only"]["doppler_1200K"] = summary(run("fuel_at_xstar_1200K", [(fuel(xf), 1.0)], 1200.0))
    out["fuel_only"]["doppler_pcm_1200_to_2100"] = worth(out["fuel_only"]["doppler_1200K"], out["fuel_only"]["at_x"])

    # ---------------- X1: Pb + W
    print("X1")
    fF, fPb, fW = x1ref["frac_fuel"], x1ref["frac_Pb"], x1ref["frac_W"]
    X1 = {"fractions": {"fuel": fF, "Pb": fPb, "W": fW}}
    comps = lambda x, pb=fPb, w=fW, wmat=None: [(fuel(x), fF), (lead(), pb), (wmat or tungsten(), w)]
    pts = [(x, run(f"X1_x{x:.2f}", comps(x))) for x in (0.12, 0.15, 0.18)]
    X1["pu_search"] = solve_x(pts)
    x1 = X1["pu_search"]["x_pu"]
    base = run("X1_ref", comps(x1))
    X1["ref"] = summary(base)
    vo = run("X1_Pb_void", [(fuel(x1), fF), (void(), fPb), (tungsten(), fW)])
    X1["Pb_void_worth"] = worth(base, vo)
    dop = run("X1_ref_1200K", comps(x1), 1200.0)
    X1["doppler_pcm_1200_to_2100"] = worth(dop, base)
    w186 = run("X1_W186", comps(x1, wmat=tungsten(0.99)))
    X1["W186_99pct_worth"] = worth(base, w186)
    X1["W186_ref"] = summary(w186)
    # fraction sweeps at fixed Pu fraction x1 (other component replaced by fuel volume)
    sw = []
    for pb in (0.0, 0.10, 0.23, 0.40):
        r = run(f"X1sw_Pb{pb:.2f}", [(fuel(x1), 1 - pb), (lead(), pb)] if pb else [(fuel(x1), 1.0)])
        sw.append({"Pb": pb, "W": 0.0, "k": r["k_inf"], "sd": r["k_inf_sd"], "cr": r["conversion_ratio"], "Emed_keV": r["median_energy_eV"] / 1e3})
    for w in (0.05, 0.10, 0.15):
        r = run(f"X1sw_W{w:.2f}", [(fuel(x1), 1 - w), (tungsten(), w)])
        sw.append({"Pb": 0.0, "W": w, "k": r["k_inf"], "sd": r["k_inf_sd"], "cr": r["conversion_ratio"], "Emed_keV": r["median_energy_eV"] / 1e3})
    X1["sweep_at_x"] = sw
    k0 = sw[0]["k"]
    X1["dk_per_0.1_vol_Pb"] = round(float(np.polyfit([s["Pb"] for s in sw[:4]], [s["k"] for s in sw[:4]], 1)[0] * 0.1), 4)
    X1["dk_per_0.1_vol_W"] = round(float(np.polyfit([0] + [s["W"] for s in sw[4:]], [k0] + [s["k"] for s in sw[4:]], 1)[0] * 0.1), 4)
    out["X1"] = X1

    # ---------------- X2: CaF2 holdup
    print("X2")
    X2 = {}
    sw = []
    for a in (0.05, 0.10, 0.20, 0.30):
        r = run(f"X2sw_a{a:.2f}", [(fuel(xf), 1 - a), (caf2(), a)])
        sw.append({"holdup": a, "k": r["k_inf"], "sd": r["k_inf_sd"], "cr": r["conversion_ratio"], "Emed_keV": r["median_energy_eV"] / 1e3,
                   "parasitic": r["parasitic_absorption_share"]})
    X2["sweep_at_fuel_only_x"] = {"x_pu": xf, "rows": sw,
                                  "dk_per_0.1_vol": round(float(np.polyfit([0] + [s["holdup"] for s in sw], [out["fuel_only"]["at_x"]["k_inf"]] + [s["k"] for s in sw], 1)[0] * 0.1), 4)}
    aref = 0.20
    pts = [(x, run(f"X2_a{aref:.2f}_x{x:.2f}", [(fuel(x), 1 - aref), (caf2(), aref)])) for x in (0.10, 0.12, 0.15)]
    X2["pu_search_holdup_0.20"] = solve_x(pts)
    x2 = X2["pu_search_holdup_0.20"]["x_pu"]
    base = run("X2_ref", [(fuel(x2), 1 - aref), (caf2(), aref)])
    X2["ref"] = summary(base)
    X2["ref_holdup"] = aref
    vo = run("X2_salt_out", [(fuel(x2), 1 - aref), (void(), aref)])
    X2["salt_void_worth"] = worth(base, vo)
    X2["doppler_pcm_1200_to_2100"] = worth(run("X2_ref_1200K", [(fuel(x2), 1 - aref), (caf2(), aref)], 1200.0), base)
    c44 = run("X2_Ca44", [(fuel(x2), 1 - aref), (caf2(ca44=True), aref)])
    X2["Ca44_99pct_worth"] = worth(base, c44)
    # holdup 0.30 Pu search point (for inventory comparisons)
    pts30 = [(x, run(f"X2_a0.30_x{x:.2f}", [(fuel(x), 0.70), (caf2(), 0.30)])) for x in (0.12, 0.15)]
    X2["pu_search_holdup_0.30"] = solve_x(pts30)
    pts10 = [(x, run(f"X2_a0.10_x{x:.2f}", [(fuel(x), 0.90), (caf2(), 0.10)])) for x in (0.10, 0.12)]
    X2["pu_search_holdup_0.10"] = solve_x(pts10)
    out["X2"] = X2

    # ---------------- X3: boiling Ca
    print("X3")
    X3 = {}
    av = 0.30  # vapour void fraction in the pool (approx., see thermal.py)
    sw = []
    for cl in (0.02, 0.05, 0.10):
        r = run(f"X3sw_Ca{cl:.2f}", [(fuel(xf), 1 - cl - av), (calcium(RHO["Ca_l"], "Ca liquid"), cl), (calcium(RHO["Ca_v"], "Ca vapour"), av)])
        sw.append({"Ca_liquid": cl, "k": r["k_inf"], "sd": r["k_inf_sd"], "cr": r["conversion_ratio"], "Emed_keV": r["median_energy_eV"] / 1e3,
                   "parasitic": r["parasitic_absorption_share"]})
    k_novap = run("X3sw_Ca0.00", [(fuel(xf), 1 - av), (calcium(RHO["Ca_v"], "Ca vapour"), av)])
    X3["sweep_at_fuel_only_x"] = {"x_pu": xf, "void": av, "rows": sw, "no_liquid": summary(k_novap),
                                  "dk_per_0.1_vol_liquid_Ca": round(float(np.polyfit([0] + [s["Ca_liquid"] for s in sw], [k_novap["k_inf"]] + [s["k"] for s in sw], 1)[0] * 0.1), 4)}
    cref = 0.05
    comps3 = lambda x, rho_l=RHO["Ca_l"]: [(fuel(x), 1 - cref - av), (calcium(rho_l, "Ca liquid"), cref), (calcium(RHO["Ca_v"], "Ca vapour"), av)]
    pts = [(x, run(f"X3_x{x:.2f}", comps3(x))) for x in (0.10, 0.12)]
    X3["pu_search"] = solve_x(pts)
    x3 = X3["pu_search"]["x_pu"]
    base = run("X3_ref", comps3(x3))
    X3["ref"] = summary(base)
    X3["ref_fractions"] = {"fuel": 1 - cref - av, "Ca_liquid": cref, "Ca_vapour_void": av}
    boil = run("X3_liquid_to_vapour", comps3(x3, rho_l=RHO["Ca_v"]))
    X3["Ca_liquid_to_vapour_worth"] = worth(base, boil)
    X3["doppler_pcm_1200_to_2100"] = worth(run("X3_ref_1200K", comps3(x3), 1200.0), base)
    out["X3"] = X3

    # Geometric (leakage) void component, one-group estimate: free-surface pool of fixed fuel mass,
    # leakage term L = M^2 B^2 = 0.15 at k_inf = 1.15 (k_eff = 1); M ~ 1/(1-a), R ~ (1-a)^(-1/3)
    # => L(a) = L0 ((1-a0)/(1-a))^(4/3); d(ln k_eff)/da = -(4/3) L/(1+L)/(1-a).
    geo = {}
    for a0 in (0.0, 0.2, 0.3):
        L = K_TARGET - 1
        geo[str(a0)] = round(-1e5 * (4 / 3) * L / (1 + L) / (1 - a0) * 0.01, 0)
    out["leakage_void_pcm_per_0.01_void"] = {"by_base_void": geo, "note": "one-group estimate (calc, approx.); pool free to swell, fixed fuel mass"}

    (HERE / "results" / "neutronics.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("fuel_only",)}, indent=1)[:1500])


if __name__ == "__main__":
    main()

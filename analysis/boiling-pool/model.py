"""Boiling-fuel ("pressure cooker") reactor: thermal-hydraulic and vessel model.

A sealed vessel holds a liquid fuel at its boiling point. Its temperature is pinned to the
saturation temperature at the vessel pressure; power rises -> more vapour -> lower fuel density
in the core -> negative reactivity. The vessel is cooled from outside by liquid aluminium.

What boils: no actinide compound or metal has vapour data in the database (JANAF has none), and
U-Pu metal boils at ~3,500-4,400 K (handbook, approx). So the boiling liquid is the *solvent* of a
fuel salt (NaCl in NaCl-(U,Pu)Cl3, LiF in LiF-(U,Pu)F4) or a carrier metal in contact with molten
U-Pu (Pb, Ca, Mg). Solvent vapour data come from NIST-JANAF in the property database (monomer,
dimer, trimer partial pressures); the actinide salt is taken as non-volatile and the solvent
follows Raoult's law (both approx).

Physics in this module:
  vapour(...)        partial pressures, total pressure, vapour density, latent heat (db)
  void_fraction(...) drift-flux void in a pool heated volumetrically, all heat leaving as vapour
  q3_for_void(...)   power density a boiling pool can carry at a given mean void
  flooding_q(...)    counter-current flooding limit per unit cross-section (Faghri et al. 1989)
  wall(...)          heat flux, temperatures and stresses through a duplex vessel wall
All correlations are APPROX and labelled; numbers they produce are (calc).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from htfbr_data import db, thermo

R = 8.314462618
G = 9.81
SIGMA_SB = 5.670374419e-8
_CON = db.connect()

M_KG = {"NaCl": 0.058443, "LiF": 0.025939, "Pb": 0.2072, "Ca": 0.040078, "Mg": 0.024305,
        "KCl": 0.074551, "CaCl2": 0.110984, "MgCl2": 0.095211}


# --------------------------------------------------------------------------- vapour (db)
def vapour(solvent: str, T: float, x: float = 1.0) -> dict:
    """Vapour over a liquid containing mole fraction x of `solvent` (Raoult; oligomer k scales x^k).

    Returns total pressure (Pa), vapour density (kg/m3), latent heat per kg of vapour (J/kg),
    mean molar mass, and the partial pressures by oligomer.
    """
    gases = thermo.gas_oligomers(_CON, solvent)
    cond = thermo.find_species(_CON, solvent, "cr,l")
    g_c = thermo.interp(_CON, cond, "dfG", T)
    h_c = thermo.enthalpy(_CON, cond, T)
    parts, n_mass, heat = {}, 0.0, 0.0
    for k, sid in gases:
        g = thermo.interp(_CON, sid, "dfG", T)
        h = thermo.enthalpy(_CON, sid, T)
        if g is None or h is None or g_c is None:
            continue
        p = math.exp(-(g - k * g_c) * 1e3 / (R * T)) * x ** k   # bar
        parts[k] = p
        n_mass += p * k * M_KG[solvent]                     # bar * kg/mol
        heat += p * (h - k * h_c) * 1e3                      # bar * J/mol
    if not parts:  # element above its JANAF boiling point: Clausius-Clapeyron from Tb (db, extrapolated)
        p, how = thermo.vapor_pressure_bar(_CON, solvent, T)
        bp = thermo.transition_T(_CON, cond, "FUGACITY")
        mono = dict(gases)[1]
        dH = (thermo.enthalpy(_CON, mono, bp) - thermo.enthalpy(_CON, cond, bp)) * 1e3
        parts = {1: p * x}
        n_mass, heat = p * x * M_KG[solvent], p * x * dH
    P_bar = sum(parts.values())
    M_mean = n_mass / P_bar
    return {"solvent": solvent, "T_K": T, "x": x, "P_Pa": P_bar * 1e5, "partials_bar": parts,
            "rho_g": P_bar * 1e5 * M_mean / (R * T), "h_fg": heat / n_mass, "M_mean": M_mean,
            "source": "db: NIST-JANAF dfG and H of condensed and gas species (oligomers)"}


def T_sat(solvent: str, P_Pa: float, x: float = 1.0, lo: float = 900.0, hi: float = 3500.0) -> float:
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if vapour(solvent, mid, x)["P_Pa"] < P_Pa else (lo, mid)
    return 0.5 * (lo + hi)


# --------------------------------------------------------------------------- liquids (approx)
@dataclass
class Liquid:
    name: str
    rho: float      # kg/m3 at operating T
    sigma: float    # N/m
    mu: float       # Pa s
    k: float        # W/m K
    note: str


def chloride_fuel(T: float, x_nacl: float = 0.30) -> Liquid:
    """NaCl-(U,Pu)Cl3 at T. Ideal molar volumes. APPROX: NaCl rho = 2139 - 0.543 T (Janz), (U,Pu)Cl3
    rho = 6375 - 1.45 T kg/m3 (UCl3 handbook-range fit), both extrapolated far above their data (< ~1,300 K)."""
    v_na = M_KG["NaCl"] / (2139.0 - 0.543 * T)
    v_u = 0.3444 / (6375.0 - 1.45 * T)
    M = x_nacl * M_KG["NaCl"] + (1 - x_nacl) * 0.3444
    rho = M / (x_nacl * v_na + (1 - x_nacl) * v_u)
    return Liquid(f"NaCl-(U,Pu)Cl3 ({100*x_nacl:.0f}/{100*(1-x_nacl):.0f} mol%)", rho,
                  max(0.191 - 7.19e-5 * T, 0.03), 1.0e-3, 0.5, "APPROX: salt properties extrapolated to ~2,000 K")


def fluoride_fuel(T: float, x_lif: float = 0.60) -> Liquid:
    """7LiF-(U,Pu)F4 at T. APPROX: LiF rho = 2358 - 0.490 T, UF4 rho = 7784 - 0.992 T kg/m3 (handbook fits)."""
    v_li = M_KG["LiF"] / (2358.0 - 0.490 * T)
    v_u = 0.31402 / (7784.0 - 0.992 * T)
    M = x_lif * M_KG["LiF"] + (1 - x_lif) * 0.31402
    rho = M / (x_lif * v_li + (1 - x_lif) * v_u)
    return Liquid(f"7LiF-(U,Pu)F4 ({100*x_lif:.0f}/{100*(1-x_lif):.0f} mol%)", rho,
                  max(0.2 - 6e-5 * T, 0.03), 2.0e-3, 1.0, "APPROX")


def metal_carrier(name: str, T: float) -> Liquid:
    """Boiling carrier metal (the fuel is a separate molten U-Pu phase below it). APPROX handbook values."""
    if name == "Pb":
        return Liquid("Pb", 11441 - 1.2795 * T, 0.52 - 1.13e-4 * (T - 600), 1.0e-3, 9.2 + 0.011 * T,
                      "APPROX OECD/NEA lead handbook correlations, extrapolated")
    if name == "Ca":
        return Liquid("Ca", 1378 - 0.23 * (T - 1115), 0.35, 0.6e-3, 30.0, "APPROX")
    if name == "Mg":
        return Liquid("Mg", 1590 - 0.26 * (T - 923), 0.50, 0.5e-3, 80.0, "APPROX")
    raise ValueError(name)


# --------------------------------------------------------------------------- boiling pool physics
def drift(liq: Liquid, rho_g: float, C0: float = 1.2) -> tuple[float, float]:
    """(C0, drift velocity v_gj m/s), churn-turbulent bubbly flow (Zuber-Findlay; APPROX)."""
    v_gj = 1.41 * (liq.sigma * G * (liq.rho - rho_g) / liq.rho ** 2) ** 0.25
    return C0, v_gj


def void_fraction(q3: float, H: float, liq: Liquid, vap: dict, C0: float = 1.2) -> dict:
    """Mean and top void fraction of a pool of depth H (m) heated uniformly at q3 (W/m3), all heat
    leaving as vapour (stagnant liquid, condensate returns elsewhere). Drift flux:
    alpha(z) = j(z) / (C0 j(z) + v_gj), j(z) = q3 z / (rho_g h_fg)."""
    C0, v = drift(liq, vap["rho_g"], C0)
    a = q3 / (vap["rho_g"] * vap["h_fg"])
    jt = a * H
    if jt <= 0:
        return {"alpha_mean": 0.0, "alpha_top": 0.0, "j_top": 0.0, "v_gj": v}
    mean = 1 / C0 - v / (C0 ** 2 * jt) * math.log(1 + C0 * jt / v)
    return {"alpha_mean": mean, "alpha_top": jt / (C0 * jt + v), "j_top": jt, "v_gj": v}


def q3_for_void(alpha: float, H: float, liq: Liquid, vap: dict, C0: float = 1.2) -> float:
    """Power density (W/m3) at which the pool's mean void reaches alpha."""
    lo, hi = 1.0, 1e10
    if alpha >= 1 / C0:
        return float("inf")
    for _ in range(100):
        mid = math.sqrt(lo * hi)
        lo, hi = (mid, hi) if void_fraction(mid, H, liq, vap, C0)["alpha_mean"] < alpha else (lo, mid)
    return lo


def flooding_q(D: float, liq: Liquid, vap: dict) -> float:
    """Counter-current flooding limit of a closed two-phase thermosyphon, W per m2 of cross-section
    (Faghri, Chen & Morgan 1989: Ku = (rho_l/rho_g)^0.14 tanh^2(Bo^0.25); APPROX, fitted on water,
    refrigerants and liquid metals, extrapolated here)."""
    dr = liq.rho - vap["rho_g"]
    Bo = D * math.sqrt(G * dr / liq.sigma)
    Ku = (liq.rho / vap["rho_g"]) ** 0.14 * math.tanh(Bo ** 0.25) ** 2
    return Ku * vap["h_fg"] * math.sqrt(vap["rho_g"]) * (liq.sigma * G * dr) ** 0.25


def condensation_h(liq: Liquid, vap: dict, L: float, dT: float) -> float:
    """Nusselt laminar film condensation on a vertical wall of height L (W/m2 K; APPROX)."""
    dT = max(dT, 1.0)
    return 0.943 * (liq.rho * (liq.rho - vap["rho_g"]) * G * vap["h_fg"] * liq.k ** 3 / (liq.mu * L * dT)) ** 0.25


# --------------------------------------------------------------------------- vessel wall
@dataclass
class WallMaterial:
    name: str
    T_melt: float
    k: float            # W/m K near 1,800-2,100 K
    E: float            # Pa, hot
    alpha: float        # 1/K mean
    nu: float
    rupture: list       # [(T_K, 10^4 h creep-rupture strength MPa)], APPROX order of magnitude
    salt: str           # compatibility with chloride fuel salt
    al: str             # compatibility with liquid Al
    note: str = ""

    def S_allow(self, T: float) -> float:
        """Allowable primary membrane stress: 2/3 of the 10^4 h rupture strength (log-linear in T), Pa."""
        pts = sorted(self.rupture)
        if T <= pts[0][0]:
            s = pts[0][1]
        elif T >= pts[-1][0]:
            (T1, s1), (T2, s2) = pts[-2], pts[-1]
            s = math.exp(math.log(s1) + (math.log(s2) - math.log(s1)) * (T - T1) / (T2 - T1))
        else:
            for (T1, s1), (T2, s2) in zip(pts, pts[1:]):
                if T1 <= T <= T2:
                    s = math.exp(math.log(s1) + (math.log(s2) - math.log(s1)) * (T - T1) / (T2 - T1))
                    break
        return 2 / 3 * s * 1e6


# APPROX: creep-rupture strengths are order-of-magnitude values from the refractory-metals literature
# (NASA/ORNL space-power programmes); to be replaced by assessed data (open question).
MATERIALS = {
    "W": WallMaterial("tungsten", 3695, 100, 330e9, 5.5e-6, 0.28, [(1600, 100), (1900, 40), (2200, 15)],
                      "noble vs chlorides (WCl6 far less stable than NaCl, UCl3)", "forms W-Al aluminides: needs a barrier"),
    "W-25Re": WallMaterial("W-25Re", 3400, 70, 330e9, 5.8e-6, 0.29, [(1600, 160), (1900, 70), (2200, 25)],
                           "as W", "as W", "ductile at room temperature; Re costly"),
    "Mo-TZM": WallMaterial("Mo (TZM)", 2896, 90, 250e9, 6.0e-6, 0.31, [(1400, 300), (1700, 70), (1900, 25)],
                           "noble vs chlorides", "forms Mo-Al aluminides: needs a barrier"),
    "Ta-10W": WallMaterial("Ta-10W / T-111", 3270, 65, 150e9, 7.0e-6, 0.35, [(1500, 100), (1800, 30), (2000, 12)],
                           "TaCl5 more stable: attack if salt is oxidising", "forms aluminides: needs a barrier"),
    "Re": WallMaterial("rhenium", 3459, 50, 400e9, 7.0e-6, 0.30, [(2000, 50), (2300, 20)],
                       "noble", "forms aluminides: needs a barrier", "very costly; strong neutron absorber"),
    "Nb-1Zr": WallMaterial("Nb-1Zr", 2750, 65, 90e9, 7.5e-6, 0.38, [(1300, 70), (1500, 25)],
                           "NbCl5 fairly stable: attack", "forms aluminides", "too weak above ~1,500 K"),
}

# Al-facing barrier layers (A-family Phase 1: saturation solubility in liquid Al exceeds the 0.1 at% margin at
# ~1,770 K for ZrB2, ~1,840 K for AlN, ~1,950 K for TiB2; calc, analysis/a-family)
BARRIERS = {
    "AlN": {"k": 30.0, "E": 310e9, "alpha": 5.3e-6, "nu": 0.24, "sigma_f": 250e6, "T_al_max": 1840.0},
    "TiB2": {"k": 60.0, "E": 500e9, "alpha": 7.5e-6, "nu": 0.11, "sigma_f": 300e6, "T_al_max": 1950.0},
    "ZrB2": {"k": 60.0, "E": 450e9, "alpha": 6.5e-6, "nu": 0.13, "sigma_f": 300e6, "T_al_max": 1770.0},
}


def wall(T_hot: float, q2: float, P_Pa: float, r: float, t_struct: float, mat: WallMaterial,
         barrier: str = "TiB2", t_barrier: float = 1.0e-3, h_al: float = 5e4, T_al: float = 1600.0) -> dict:
    """Duplex wall: structural refractory metal (fuel side) + ceramic barrier (Al side).

    Given the fuel-side surface temperature and the heat flux, returns the temperature drops, the
    Al-side surface temperature, the primary hoop stress (thin shell, P r / t) against 2/3 of the
    rupture strength at the wall mean temperature, and the thermal stresses of both layers
    (E alpha dT / 2(1-nu)) against limits: metal 3 S_allow (secondary, relaxes), ceramic fracture/2.
    """
    b = BARRIERS[barrier]
    dT_m = q2 * t_struct / mat.k
    dT_b = q2 * t_barrier / b["k"]
    T_mid = T_hot - dT_m
    T_al_face = T_mid - dT_b
    Tm = T_hot - 0.5 * dT_m
    sig_p = P_Pa * r / t_struct
    S = mat.S_allow(Tm)
    sig_th_m = mat.E * mat.alpha * dT_m / (2 * (1 - mat.nu))
    sig_th_b = b["E"] * b["alpha"] * dT_b / (2 * (1 - b["nu"]))
    T_al_needed = T_al_face - q2 / h_al
    return {"dT_metal": dT_m, "dT_barrier": dT_b, "T_al_face": T_al_face, "T_al_bulk_max": T_al_needed,
            "sigma_p_MPa": sig_p / 1e6, "S_allow_MPa": S / 1e6, "sigma_th_metal_MPa": sig_th_m / 1e6,
            "sigma_th_barrier_MPa": sig_th_b / 1e6,
            "ok_primary": sig_p <= S, "ok_thermal_metal": sig_th_m <= 3 * S, "ok_barrier": sig_th_b <= b["sigma_f"] / 2,
            "ok_al_dissolution": T_al_face <= b["T_al_max"]}


def max_flux(T_hot: float, P_Pa: float, r: float, mat: WallMaterial, barrier: str = "TiB2",
             t_barrier: float = 1.0e-3, h_al: float = 5e4, T_al: float = 1600.0) -> dict:
    """Largest heat flux through the wall with all four checks met, optimising the metal thickness
    (pressure wants it thick, thermal stress wants it thin)."""
    best = None
    for t_mm in [0.5 * 1.15 ** i for i in range(40)]:
        t = t_mm / 1e3
        if P_Pa * r / t > mat.S_allow(T_hot):   # cannot hold the pressure even cold-side-less
            continue
        lo, hi = 0.0, 50e6
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            w = wall(T_hot, mid, P_Pa, r, t, mat, barrier, t_barrier, h_al, T_al)
            ok = (w["ok_primary"] and w["ok_thermal_metal"] and w["ok_barrier"]
                  and w["T_al_bulk_max"] >= T_al and w["T_al_face"] <= BARRIERS[barrier]["T_al_max"])
            lo, hi = (mid, hi) if ok else (lo, mid)
        if lo > 0 and (best is None or lo > best[0]):
            best = (lo, t, wall(T_hot, lo, P_Pa, r, t, mat, barrier, t_barrier, h_al, T_al))
    if best is None:
        return {"q2_max": 0.0, "t_struct": None, "limits": "pressure stress exceeds the allowable at any thickness tried"}
    q, t, w = best
    w2 = wall(T_hot, q * 1.01, P_Pa, r, t, mat, barrier, t_barrier, h_al, T_al)
    limits = [n for n, okk in (("pressure", w2["ok_primary"]), ("metal thermal stress", w2["ok_thermal_metal"]),
                                ("barrier thermal stress", w2["ok_barrier"]), ("Al-side temperature", w2["T_al_bulk_max"] >= T_al),
                                ("barrier dissolution in Al", w2["T_al_face"] <= BARRIERS[barrier]["T_al_max"])) if not okk]
    return {"q2_max": q, "t_struct": t, "wall": w, "limits": ", ".join(limits) or "thickness range"}

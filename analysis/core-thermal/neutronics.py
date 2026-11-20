"""One-group diffusion core model with OpenMC-collapsed constants (constants.py).

Answers, for a homogenised core composition at given fuel and coolant temperatures:
  k_inf, migration area, critical size (bare or reflected sphere, bare cylinder), fissile and
  heavy-metal inventory, conversion ratio (core only), power shape and peaking, energy deposited
  per fission and per capture (ENDF MF1/MT458 and MT102 Q values), flux per unit power,
  delayed-neutron data (beta_i, lambda_i) and prompt generation time, and reactivity coefficients
  (Doppler, fuel density, coolant density) by finite differences of the same model.

Spectrum: microscopic one-group constants are interpolated between the hard / medium / soft
references in ln(moderating ratio), and between 1200 and 2100 K in ln(T) (extrapolated outside,
flagged). Each nuclide takes the temperature of the component it sits in, so the fuel
temperature drives Doppler and the coolant temperature only changes coolant density.

Limits: one group, homogenised, no spatial self-shielding, no blanket breeding; diffusion
overstates leakage error for small cores (checked against Godiva in validate.py).
"""
from __future__ import annotations

import json
import os
import math
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import numpy as np
import openmc
import openmc.data

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
import importlib.util as _ilu  # load new-geometries/materials.py by path (its folder also has a thermal.py)
_spec = _ilu.spec_from_file_location("ng_materials", ROOT / "analysis" / "new-geometries" / "materials.py")
M = _ilu.module_from_spec(_spec)
sys.modules["ng_materials"] = M
_spec.loader.exec_module(M)  # shared Pu vector, U vector, natural abundances, densities

CONSTANTS = Path(os.environ.get("CORE_CONSTANTS", HERE / "results" / "constants.json"))
LIB = ROOT / "data" / "openmc"
FISSILE = ("U233", "U235", "Pu239", "Pu241")
FERTILE = ("Th232", "U234", "U238", "Pu238", "Pu240", "Pu242")
MEV = 1.602176634e-13  # J
BARN = 1e-24           # cm2
NA = 6.02214076e23


# --------------------------------------------------------------------------- compositions
def fuel_material(form: str, pu: float, rho_gcc: float | None = None) -> openmc.Material:
    """form: UPu_liquid | UPuZr | UPuN | UPuO2. pu = Pu/(U+Pu) atom fraction."""
    m = openmc.Material(name=f"{form} pu={pu:.3f}")
    M.heavy_metal(m, pu)
    if form == "UPuN":
        m.add_nuclide("N15", M.N15_ENRICHMENT)
        m.add_nuclide("N14", 1 - M.N15_ENRICHMENT)
        rho = rho_gcc or 13.6
    elif form == "UPuO2":
        m.add_nuclide("O16", 2.0)
        rho = rho_gcc or 10.4
    elif form == "UPuZr":  # 10 wt% Zr ~ 23 at%
        for nuc, f in M.natural("Zr").items():
            m.add_nuclide(nuc, 0.30 * f)
        rho = rho_gcc or 15.8
    elif form == "UPu_liquid":
        rho = rho_gcc or 16.0
    else:
        raise ValueError(form)
    m.set_density("g/cm3", rho)
    return m


def element_material(symbol_or_formula: str, rho_gcc: float) -> openmc.Material:
    m = openmc.Material(name=symbol_or_formula)
    if symbol_or_formula == "He":
        m.add_nuclide("He4", 1.0)
    elif symbol_or_formula == "Al":
        m.add_nuclide("Al27", 1.0)
    elif symbol_or_formula == "Na":
        m.add_nuclide("Na23", 1.0)
    elif symbol_or_formula == "FLiBe":
        m.add_nuclide("Li7", 2 * 0.9999); m.add_nuclide("Li6", 2 * 0.0001)
        m.add_nuclide("Be9", 1.0); m.add_nuclide("F19", 4.0)
    elif symbol_or_formula == "AlN":
        m.add_nuclide("Al27", 1.0); m.add_nuclide("N15", M.N15_ENRICHMENT); m.add_nuclide("N14", 1 - M.N15_ENRICHMENT)
    elif symbol_or_formula == "SiC":
        for nuc, f in M.natural("Si").items():
            m.add_nuclide(nuc, f)
        m.add_nuclide("C12", 1.0)
    elif symbol_or_formula == "steel":
        for el, w in (("Fe", 0.71), ("Cr", 0.17), ("Ni", 0.12)):
            for nuc, f in M.natural(el).items():
                m.add_nuclide(nuc, w * f, "wo")
    else:
        for nuc, f in M.natural(symbol_or_formula).items():
            m.add_nuclide(nuc, f)
    m.set_density("g/cm3", rho_gcc)
    return m


@dataclass
class Region:
    """A homogenised core: named components with volume fractions and temperatures."""
    parts: list = field(default_factory=list)  # (role, openmc.Material, volume fraction, T_K)

    def add(self, role, mat, frac, T):
        self.parts.append((role, mat, frac, T))
        return self

    def densities(self) -> list[tuple[str, str, float, float]]:
        """[(role, nuclide, atoms/b-cm in the homogenised core, T)]"""
        out = []
        for role, mat, frac, T in self.parts:
            for nuc, n in mat.get_nuclide_atom_densities().items():
                out.append((role, nuc, n * frac, T))
        return out

    def scaled(self, role, factor, T=None):
        """Copy with one component's density scaled (thermal expansion, voiding) and/or new T."""
        r = Region()
        for ro, mat, frac, t in self.parts:
            if ro == role:
                r.add(ro, mat, frac * factor, T if T is not None else t)
            else:
                r.add(ro, mat, frac, t)
        return r

    def at(self, role, T):
        return self.scaled(role, 1.0, T)


# --------------------------------------------------------------------------- constants
@lru_cache(None)
def _const():
    if not CONSTANTS.exists():
        raise FileNotFoundError(f"{CONSTANTS} missing: run constants.py")
    d = json.loads(CONSTANTS.read_text())
    d.pop("_meta", None)
    return d


@lru_cache(None)
def _A(nuc):
    return openmc.data.atomic_mass(nuc) / openmc.data.NEUTRON_MASS if hasattr(openmc.data, "NEUTRON_MASS") else openmc.data.atomic_mass(nuc) / 1.00866491595


def _xi(nuc):
    A = _A(nuc)
    if A < 1.01:
        return 1.0
    a = ((A - 1) / (A + 1)) ** 2
    return 1 + a * math.log(a) / (1 - a)


def refs() -> list[str]:
    return sorted({k.split(":")[0] for k in _const()}, key=lambda r: -_const()[f"{r}:1200"]["median_energy_eV"])


GROUPED = {"total": "total", "absorption": "absorption", "fission": "fission", "nu_fission": "nu-fission",
           "capture": "(n,gamma)", "n2n": "(n,2n)"}


@lru_cache(None)
def _collapsed(ref, nuc, key):
    """(sigma at 1200 K, sigma at 2100 K) collapsed from fine groups with ONE spectrum: the mean of the
    two runs' normalised group fluxes. Run-to-run spectrum noise then cannot pose as Doppler."""
    c = _const()
    r1, r2 = c[f"{ref}:1200"], c[f"{ref}:2100"]
    f1, f2 = np.array(r1["flux_g"]), np.array(r2["flux_g"])
    w = 0.5 * (f1 / f1.sum() + f2 / f2.sum())
    g1 = np.array(r1["sigma_b"][nuc]["groups"][GROUPED[key]])
    g2 = np.array(r2["sigma_b"][nuc]["groups"][GROUPED[key]])
    return float(np.dot(w, g1)), float(np.dot(w, g2))


def _sig(ref, T, nuc, key):
    """Microscopic one-group value at reference spectrum ref, interpolated in ln T."""
    c = _const()
    lo, hi = c[f"{ref}:1200"]["sigma_b"][nuc], c[f"{ref}:2100"]["sigma_b"][nuc]
    w = (math.log(T) - math.log(1200.0)) / (math.log(2100.0) - math.log(1200.0))
    if key in GROUPED and "groups" in lo:
        a, b = _collapsed(ref, nuc, key)
        return a + w * (b - a)
    a, b = lo[key], hi[key]
    if isinstance(a, list):
        return [x + w * (y - x) for x, y in zip(a, b)]
    return a + w * (b - a)


def _s1(ref, T, nuc):
    """Elastic P1 moment: the data-derived value (p1data.py) for every nuclide, for consistency
    between present and trace nuclides; validate.py compares it with the analog tally."""
    return _sig(ref, T, nuc, "scatter_p1_data")


def moderating_ratio(dens, ref="medium") -> float:
    """sum(xi * Sigma_s) / sum(Sigma_a) of a composition, with the medium reference's sigmas at 1200 K."""
    num = den = 0.0
    for _, nuc, n, _T in dens:
        num += n * _xi(nuc) * _sig(ref, 1200.0, nuc, "scatter")
        den += n * _sig(ref, 1200.0, nuc, "absorption")
    return num / den


@lru_cache(None)
def _ref_index():
    """ln(moderating ratio) of each reference recipe (rebuilt from constants.py's recipes)."""
    import constants as C
    out = {}
    for r in refs():
        comps = C.REFERENCES[r]()
        reg = Region()
        for m, f in comps:
            reg.add(m.name, m, f, 1200.0)
        out[r] = math.log(moderating_ratio(reg.densities()))
    return out


def spectrum_weights(dens) -> tuple[dict, str]:
    """Interpolation weights over references for this composition, and a note if extrapolated."""
    idx = _ref_index()
    x = math.log(moderating_ratio(dens))
    order = sorted(idx, key=idx.get)  # hard (low ratio) ... soft (high ratio)
    if x <= idx[order[0]]:
        return {order[0]: 1.0}, f"harder than '{order[0]}' reference: clamped"
    if x >= idx[order[-1]]:
        return {order[-1]: 1.0}, f"softer than '{order[-1]}' reference: clamped"
    for a, b in zip(order, order[1:]):
        if idx[a] <= x <= idx[b]:
            w = (x - idx[a]) / (idx[b] - idx[a])
            return {a: 1 - w, b: w}, ""
    raise RuntimeError


def micro(dens, nuc, T, key, weights):
    vals = [(w, _sig(r, T, nuc, key) if key != "s1" else _s1(r, T, nuc)) for r, w in weights.items()]
    if isinstance(vals[0][1], list):
        return [sum(w * v[i] for w, v in vals) for i in range(len(vals[0][1]))]
    return sum(w * v for w, v in vals)


@lru_cache(None)
def _energy(nuc):
    """(recoverable energy per fission, Q of (n,gamma)) in MeV, from the evaluation (MT458, MT102)."""
    d = openmc.data.IncidentNeutron.from_hdf5(str(LIB / f"{nuc}.h5"))
    ef = d.fission_energy.recoverable(1e5) / 1e6 if d.fission_energy is not None else 0.0
    qc = d.reactions[102].q_value / 1e6 if 102 in d.reactions else 0.0
    return ef, qc


# --------------------------------------------------------------------------- one-group core
@dataclass
class OneGroup:
    k_inf: float
    D: float            # cm
    sig_a: float        # 1/cm (net of n,2n)
    nu_sig_f: float     # 1/cm
    sig_f: float
    M2: float           # cm2
    cr: float           # conversion ratio proxy (core only)
    beta: list          # 6 groups
    lam: list           # 1/s
    beta_eff: float
    gen_time: float     # s
    J_per_fission_rate: float   # J per (fission/cm3/s) incl. capture gammas -> q''' = this * Sigma_f * phi
    fissile_kg_m3: float
    hm_kg_m3: float
    weights: dict
    note: str


def one_group(region: Region) -> OneGroup:
    dens = region.densities()
    weights, note = spectrum_weights(dens)
    sa = nsf = sf = st = 0.0
    fis_abs = fert_cap = 0.0
    dnf = np.zeros(6)
    dlam = np.zeros(6)
    energy = 0.0
    fissile_mass = hm_mass = 0.0
    for role, nuc, n, T in dens:
        g = lambda k: micro(dens, nuc, T, k, weights)
        a, f, nf, c = g("absorption"), g("fission"), g("nu_fission"), g("capture")
        n2n = g("n2n")
        sa += n * (a - n2n)
        nsf += n * nf
        sf += n * f
        st += n * (g("total") - g("s1"))
        if nuc in FISSILE:
            fis_abs += n * a
        if nuc in FERTILE:
            fert_cap += n * (a - f)
        if nf > 0:
            b, l = np.array(g("beta")), np.array(g("lambda"))
            dnf += n * nf * b
            dlam += n * nf * b * l
        ef, qc = _energy(nuc)
        energy += n * (f * ef + c * qc)
        mass_g = n * 1e24 / NA * openmc.data.atomic_mass(nuc)  # g/cm3
        if nuc in FISSILE:
            fissile_mass += mass_g
        if nuc.startswith(("U", "Pu", "Th", "Am")):
            hm_mass += mass_g
    D = 1.0 / (3.0 * st)
    nsf_ = nsf or 1e-300
    beta = dnf / nsf_
    lam = np.divide(dlam, dnf, out=np.zeros(6), where=dnf > 0)
    inv_v = sum(w * _const()[f"{r}:1200"]["inverse_velocity_s_per_cm"] for r, w in weights.items())
    return OneGroup(
        k_inf=nsf / sa, D=D, sig_a=sa, nu_sig_f=nsf, sig_f=sf, M2=D / sa,
        cr=fert_cap / fis_abs if fis_abs else float("nan"),
        beta=beta.tolist(), lam=lam.tolist(), beta_eff=float(beta.sum()),
        gen_time=inv_v / nsf_,
        J_per_fission_rate=energy / (sf or 1e-300) * MEV,  # MeV per fission (incl. captures) -> J
        fissile_kg_m3=fissile_mass * 1e3, hm_kg_m3=hm_mass * 1e3, weights=weights, note=note)


# --------------------------------------------------------------------------- criticality
def bare_sphere_radius(g: OneGroup) -> float:
    """Critical radius (cm) of a bare sphere; extrapolation distance 2.13 D."""
    if g.k_inf <= 1:
        return float("inf")
    B = math.sqrt((g.k_inf - 1) / g.M2)
    return math.pi / B - 2.13 * g.D


def reflected_sphere_radius(g: OneGroup, refl: OneGroup, thickness_cm: float) -> float:
    """Critical core radius with a reflector (one-group, two-region sphere).

    Reflector removal uses sigma_a - nu*sigma_f, so a fertile blanket counts as a weakly
    absorbing reflector. Outer boundary: zero flux at thickness + 2.13 D_r.
    """
    if g.k_inf <= 1:
        return float("inf")
    B = math.sqrt((g.k_inf - 1) / g.M2)
    kap = math.sqrt(max(refl.sig_a - refl.nu_sig_f, 1e-12) / refl.D)
    T = thickness_cm + 2.13 * refl.D

    def f(R):
        return g.D * (B / math.tan(B * R) - 1 / R) + refl.D * (kap / math.tanh(kap * T) + 1 / R)
    lo, hi = 1e-3, math.pi / B * (1 - 1e-9)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def bare_cylinder(g: OneGroup, h_over_d: float = 1.0) -> tuple[float, float]:
    """Critical (radius, height) in cm of a bare cylinder with H/D fixed."""
    if g.k_inf <= 1:
        return float("inf"), float("inf")
    B2 = (g.k_inf - 1) / g.M2
    d = 2.13 * g.D

    def B2_of(R):
        H = 2 * R * h_over_d
        return (2.405 / (R + d)) ** 2 + (math.pi / (H + 2 * d)) ** 2
    lo, hi = 0.1, 1e5
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if B2_of(mid) > B2:
            lo = mid
        else:
            hi = mid
    return lo, 2 * lo * h_over_d


def sphere_peaking(g: OneGroup, R: float, reflected: bool) -> float:
    """Peak-to-average power of the fundamental mode inside the core sphere (no zoning)."""
    B = math.sqrt(max(g.k_inf - 1, 1e-12) / g.M2)
    X = B * R
    avg = 3 * (math.sin(X) - X * math.cos(X)) / X**3
    return 1.0 / avg


def k_eff_sphere(g: OneGroup, R: float, refl: OneGroup | None = None, thickness_cm: float = 0.0) -> float:
    """k_eff of a sphere of radius R (cm): bisection on k so that the critical radius equals R."""
    def radius_for(k):
        gg = OneGroup(**{**g.__dict__, "nu_sig_f": g.nu_sig_f / k, "k_inf": g.k_inf / k})
        return reflected_sphere_radius(gg, refl, thickness_cm) if refl else bare_sphere_radius(gg)
    lo, hi = 0.2, g.k_inf * (1 - 1e-9)
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if radius_for(mid) > R:  # k too large -> required radius too large
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def reactivity_pcm(k):
    return 1e5 * (k - 1) / k

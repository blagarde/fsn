"""Elastic-scattering P1 (lab-frame mean cosine) from the nuclear data, for the transport correction.

Trace nuclides in constants.py never collide, so their analog scatter-moment tallies are empty.
Instead, sigma_s1 = <sigma_el(E) * mubar_lab(E)>_phi, with mubar_lab from the ENDF/B-VIII.0
elastic angular distribution (centre-of-mass) converted to the lab frame exactly,
  mu_lab = (1 + A mu_cm) / sqrt(A^2 + 2 A mu_cm + 1),
and averaged over the reference spectrum. Inelastic and other scattering are taken as isotropic
in the lab (P1 = 0), a small error for fast spectra (inelastic is a minor share of transport).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import openmc.data

LIB = Path(__file__).resolve().parents[2] / "data" / "openmc"


@lru_cache(None)
def _nuc(name):
    return openmc.data.IncidentNeutron.from_hdf5(str(LIB / f"{name}.h5"))


def _mubar_lab(dist, A):
    """Mean lab cosine at each tabulated incident energy of an UncorrelatedAngleEnergy."""
    ang = dist.angle
    out = []
    for mu_d in ang.mu:
        x = np.asarray(mu_d.x)
        p = np.asarray(mu_d.p)
        xf = np.linspace(-1, 1, 801)
        if getattr(mu_d, "interpolation", "linear-linear") == "histogram":
            idx = np.clip(np.searchsorted(x, xf, side="right") - 1, 0, len(p) - 1)
            pf = p[idx]
        else:
            pf = np.interp(xf, x, p)
        lab = (1 + A * xf) / np.sqrt(A * A + 2 * A * xf + 1)
        w = np.trapezoid(pf, xf)
        out.append(np.trapezoid(pf * lab, xf) / w if w > 0 else 2 / (3 * A))
    return np.asarray(ang.energy), np.asarray(out)


def sigma_s1(name: str, T_key: str, edges: np.ndarray, flux: np.ndarray) -> tuple[float, float]:
    """(flux-weighted elastic sigma, flux-weighted elastic sigma * mubar_lab), barns."""
    n = _nuc(name)
    A = n.atomic_weight_ratio
    el = n.reactions[2]
    xs = el.xs[T_key]
    mid = np.sqrt(edges[:-1] * edges[1:])
    # 5 sub-points per group (log), to follow resonance structure roughly; flux constant within group
    sub = np.exp(np.linspace(0, 1, 7)[1:-1, None] * np.log(edges[1:] / edges[:-1]) + np.log(edges[:-1]))
    sig = np.asarray(xs(sub)).mean(axis=0)
    E_mu, mu = _mubar_lab(el.products[0].distribution[0], A)
    mub = np.interp(mid, E_mu, mu)
    w = flux / flux.sum()
    return float(np.dot(w, sig)), float(np.dot(w, sig * mub))

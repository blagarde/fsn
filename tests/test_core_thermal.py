"""Unit checks of the core nuclear-thermal model (analysis/core-thermal) against closed forms."""
import importlib
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis" / "core-thermal"))
TH = importlib.import_module("thermal")
P = importlib.import_module("props")


def _cell(shape, k=20.0, nu=1.0):
    fuel = P.Solid("f", 10000.0, lambda T: 300.0, lambda T: k, 3000.0, 1e-5)
    wall = P.Solid("w", 8000.0, lambda T: 500.0, lambda T: 25.0, 2000.0, 1e-5)
    return TH.Cell(shape, 3e-3, 0.5e-3, wall, fuel, nu_fuel=nu)


@pytest.mark.parametrize("shape,n", [("slab", 2), ("cylinder", 4), ("sphere", 6)])
def test_fuel_rise_matches_qa2_over_nk(shape, n):
    c = _cell(shape)
    g = TH.geometry(c, 0.4, 0.4)
    q3 = 5e8
    rise = TH.fuel_center_T(c, q3, 1000.0, g["G"]) - 1000.0
    assert rise == pytest.approx(q3 * 3e-3 ** 2 / (n * 20.0), rel=1e-3)


def test_liquid_nusselt_scales_rise():
    c1, c4 = _cell("cylinder"), _cell("cylinder", nu=4.0)
    G = TH.geometry(c1, 0.4, 0.4)["G"]
    r1 = TH.fuel_center_T(c1, 5e8, 1000.0, G) - 1000
    r4 = TH.fuel_center_T(c4, 5e8, 1000.0, G) - 1000
    assert r4 == pytest.approx(r1 / 4, rel=1e-3)


def test_radiative_gap_balance():
    c = _cell("cylinder")
    c.radiative = (0.8, 0.8)
    Th = TH.gap_hot_T(c, 5e5, 1600.0)
    q = TH.SIGMA * (Th ** 4 - 1600.0 ** 4) / (1 / 0.8 + 1 / 0.8 - 1)
    assert q == pytest.approx(5e5, rel=1e-9)


def test_annulus_fractions_consistent():
    c = _cell("annulus")
    c.a, c.wall_t = 6e-3, 1e-3
    g = TH.geometry(c, 0.45, 0.38)
    assert g["r_cell"] > c.a and g["f_wall"] > 0


def test_delayed_retention_limits():
    core = pytest.importorskip("core")  # needs scipy and openmc (nuc environment)
    beta, lam = [1.0] * 2, [0.0124, 3.0]
    assert core.delayed_retention(beta, lam, 1e3, 1e-6) == pytest.approx([1.0, 1.0], abs=2e-3)
    slow = core.delayed_retention(beta, lam, 1.0, 1.0)
    assert 0.45 < slow[0] < 0.55          # long-lived group: about the core residence share
    assert slow[1] > slow[0]


def test_decay_heat_fit():
    K = pytest.importorskip("kinetics")
    import numpy as np
    mus, A = K.decay_groups()
    core = importlib.import_module("core")
    for t in (10.0, 1e3, 1e5):
        assert (A * np.exp(-mus * t)).sum() == pytest.approx(core.decay_heat_fraction(t), rel=0.1)

from pathlib import Path

import numpy as np
import pytest

from htfbr_data import checks
from htfbr_data.chem import parse_formula
from htfbr_data.db import connect
from htfbr_data.ingest import janaf, livechart, manual

FIX = Path(__file__).parent / "fixtures"


def test_parse_formula():
    assert parse_formula("Al2O3") == {"Al": 2, "O": 3}
    assert parse_formula("Al1N1") == parse_formula("AlN")
    assert parse_formula("Ca1F2(cr,l)") == {"Ca": 1, "F": 2}
    with pytest.raises(ValueError):
        parse_formula("Xx2")


def test_livechart_parse():
    rows = {(r["z"], r["a"]): r for r in livechart.parse((FIX / "livechart_head.csv").read_text())}
    al = rows[(13, 27)]
    assert al["stable"] == 1 and al["abundance_pct"] == 100 and al["half_life_s"] is None
    assert al["atomic_mass_uu"] == pytest.approx(26981538.408)


def test_janaf_table_with_transition_rows():
    header, rows = janaf.parse_table((FIX / "janaf_Al-004.txt").read_text())
    assert header["formula"] == "Al1(cr,l)"
    melt = [r for r in rows if r["note"] and "LIQUID" in r["note"]]
    assert melt and melt[0]["T_K"] == pytest.approx(933.45)
    assert rows[0]["gef"] is None  # INFINITE at 0 K
    boil = [r for r in rows if r["note"] and "FUGACITY" in r["note"]]
    assert boil and boil[0]["T_K"] == pytest.approx(2790.812)


def test_janaf_index_parse():
    page = ('<tr><td>7429-90-5</td><td>Al</td><td>Aluminum</td><td>cr,l</td>'
            '<td><a href="Al-004.html">view</a></td><td>x</td></tr>')
    assert janaf.parse_index(page) == [
        {"cas": "7429-90-5", "formula": "Al", "name": "Aluminum", "phase": "cr,l", "table_id": "Al-004"}]


def test_manual_validation():
    q = {"density": "kilogram / meter ** 3", "melting_point": "kelvin"}
    row = {"material": "Al(l)", "quantity": "density", "value": "2.375", "unit": "g/cm**3",
           "source_id": "literature", "locator": "doi:10.x/y"}
    out = manual.validate_row(row, q, {"literature"})
    assert out["value_si"] == pytest.approx(2375)
    t = manual.validate_row({**row, "quantity": "melting_point", "value": "660.32", "unit": "degC"}, q, {"literature"})
    assert t["value_si"] == pytest.approx(933.47)
    with pytest.raises(ValueError, match="locator"):
        manual.validate_row({**row, "locator": ""}, q, {"literature"})
    with pytest.raises(ValueError, match="unregistered"):
        manual.validate_row(row, q, set())


def test_xi_formula():
    assert checks._xi(1.0001) == pytest.approx(1.0, abs=1e-3)
    assert checks._xi(12.0) == pytest.approx(0.158, abs=1e-3)


def test_endf_averages_on_1_over_v():
    """A 1/v cross section must average to the textbook Maxwellian factor sqrt(pi)/2 relative to 2200 m/s
    for the density-weighted average; for our flux weighting E exp(-E/kT) it is sqrt(pi)/2 * sqrt(E0/kT)."""
    pytest.importorskip("openmc")
    from htfbr_data.ingest.endf_xs import averages, K_B

    class OneOverV:
        x = np.geomspace(1e-5, 2e7, 20000)

        def __call__(self, e):
            return 1.0 * np.sqrt(0.0253 / np.asarray(e))

    T = 293.6
    out = averages(OneOverV(), T)
    assert out["thermal_2200"] == pytest.approx(1.0)
    expected = np.sqrt(np.pi) / 2 * np.sqrt(0.0253 / (K_B * T))
    assert out["maxwell_flux"] == pytest.approx(expected, rel=2e-3)
    # resonance integral of 1/v from 0.5 eV: 2 * sqrt(0.0253/0.5) (upper limit negligible)
    assert out["ri_1overE"] == pytest.approx(2 * np.sqrt(0.0253 / 0.5), rel=1e-3)


def test_schema_creates(tmp_path):
    con = connect(tmp_path / "t.sqlite")
    names = {r[0] for r in con.execute("SELECT name FROM sqlite_master")}
    assert {"source", "artifact", "nuclide", "species", "thermo", "xs_avg", "property", "v_xs_natural"} <= names

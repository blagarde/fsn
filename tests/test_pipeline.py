"""Tests for the parts that touch the database, the network layer and derived thermochemistry."""
import functools
import http.server
import io
import math
import threading
import zipfile

import pytest

from htfbr_data import checks, fetch, registry, thermo
from htfbr_data.db import connect
from htfbr_data.ingest import manual

R = thermo.R


@pytest.fixture
def con(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch, "RAW_DIR", tmp_path / "raw")
    c = connect(tmp_path / "t.sqlite")
    registry.load(c)
    return c


def _add_species(con, formula, phase, rows, table_id):
    """rows: list of (T, dfG, dfH, h_rel, note)."""
    cur = con.execute("INSERT INTO species (formula, phase, name, table_id) VALUES (?,?,?,?)",
                      (formula, phase, formula, table_id))
    sid = cur.lastrowid
    for i, (T, dfG, dfH, h_rel, note) in enumerate(rows):
        con.execute("INSERT INTO thermo (species_id, row_index, T_K, dfG, dfH, h_rel, note) VALUES (?,?,?,?,?,?,?)",
                    (sid, i, T, dfG, dfH, h_rel, note))
    return sid


# ---------- thermochemistry ----------

def _element_with_known_vapour(con, dH=100.0, dS=0.1, Tb=1000.0):
    """Synthetic element (Kr used as a placeholder symbol) with dfG(g) = dH - T dS (condensed reference = 0), so p = exp(-(dH - T dS)/RT).
    Tb is placed where p = 1 bar: Tb = dH/dS."""
    Ts = [298.15, 500.0, 750.0, Tb]
    _add_species(con, "Kr", "cr,l", [(T, 0.0, 0.0, 0.0, "FUGACITY = 1 bar" if T == Tb else None) for T in Ts], "X-1")
    # h_rel(gas) chosen so H_gas - H_cond = dH at every T
    _add_species(con, "Kr", "g", [(T, dH - T * dS, dH, 0.0, None) for T in Ts], "X-2")


def test_vapour_pressure_matches_analytic(con):
    _element_with_known_vapour(con)
    p, basis = thermo.vapor_pressure_bar(con, "Kr", 750.0)
    assert p == pytest.approx(math.exp(-(100.0 - 750.0 * 0.1) / (R * 750.0)), rel=1e-9)
    assert "monomer" in basis


def test_vapour_pressure_extrapolates_above_tb(con):
    _element_with_known_vapour(con)
    p, basis = thermo.vapor_pressure_bar(con, "Kr", 1200.0)
    assert basis.startswith("EXTRAPOLATED")
    assert p == pytest.approx(math.exp(-100.0 / R * (1 / 1200.0 - 1 / 1000.0)), rel=1e-6)


def test_ions_are_not_counted_as_vapour(con):
    _add_species(con, "Al", "cr,l", [(298.15, 0, 0, 0, None), (1500, 0, 0, 0, None)], "Al-a")
    _add_species(con, "Al", "g", [(298.15, 290, 330, 0, None), (1500, 160, 320, 0, None)], "Al-b")
    _add_species(con, "Al+", "g", [(298.15, 900, 910, 0, None), (1500, 800, 905, 0, None)], "Al-c")
    _add_species(con, "Al2", "g", [(298.15, 450, 480, 0, None), (1500, 330, 470, 0, None)], "Al-d")
    ks = [k for k, _ in thermo.gas_oligomers(con, "Al")]
    assert ks == [1, 2]  # the Al+ ion must not appear as a second monomer


def test_boiling_point_from_total_pressure(con):
    # compound AB with monomer only; dfG(g) - dfG(cond) = 200 - 0.1 T -> 1 bar at 2000 K
    Ts = [298.15, 1000.0, 1500.0, 2500.0]
    _add_species(con, "LiF", "cr,l", [(T, -600.0, -600.0, 0.0, None) for T in Ts], "LiF-1")
    _add_species(con, "LiF", "g", [(T, -600.0 + 200 - 0.1 * T, -400.0, 0.0, None) for T in Ts], "LiF-2")
    T, basis = thermo.boiling_point_K(con, "LiF")
    assert T == pytest.approx(2000.0, abs=2.0)
    assert "total p" in basis


def test_melting_point_from_transition_row(con):
    _add_species(con, "Al", "cr,l", [(298.15, 0, 0, 0, None), (933.45, 0, 0, 18.0, "CRYSTAL <--> LIQUID"),
                                     (933.45, 0, 0, 28.7, "TRANSITION")], "Al-e")
    T, _ = thermo.melting_point_K(con, "Al")
    assert T == pytest.approx(933.45)


# ---------- claims checker ----------

def test_claims_evaluate_half_life_and_dfg(con):
    con.execute("INSERT INTO nuclide (z, a, symbol, stable, half_life_s, half_life_text) VALUES (13, 28, 'Al', 0, 134.7, '2.245 m')")
    v, unit, _ = checks.evaluate(con, {"kind": "half_life", "nuclide": "Al-28", "value": 2.2, "unit": "min"})
    assert unit == "min" and v == pytest.approx(134.7 / 60)

    _add_species(con, "Al2O3", "cr", [(298.15, -1582.3, -1675.7, 0, None)], "Al-f")
    v, unit, _ = checks.evaluate(con, {"kind": "dfG_per_O2", "formula": "Al2O3", "phase": "cr", "T_K": 298.15, "value": 1055})
    assert v == pytest.approx(1582.3 / 1.5)

    v, _, basis = checks.evaluate(con, {"kind": "dfG_per_O2", "formula": "Y2O3", "phase": "cr", "T_K": 298.15, "value": 1211})
    assert v is None and "not in NIST-JANAF" in basis


def test_natural_xs_requires_full_coverage(con):
    # Sn-like element with only one of two isotopes processed -> not checkable
    con.executemany("INSERT INTO nuclide (z, a, symbol, abundance_pct, stable) VALUES (?,?,?,?,1)",
                    [(50, 118, "Sn", 60.0), (50, 120, "Sn", 40.0)])
    con.execute("INSERT INTO weighting VALUES ('thermal_2200','d','d',NULL)")
    con.execute("INSERT INTO xs_avg VALUES (50,118,'endfb80',102,'capture','thermal_2200',293.6,0.2,'m',NULL)")
    claim = {"kind": "xs_element", "element": "Sn", "mt": 102, "weighting": "thermal_2200", "value": 0.63}
    v, _, basis = checks.evaluate(con, claim)
    assert v is None and "60.00%" in basis
    con.execute("INSERT INTO xs_avg VALUES (50,120,'endfb80',102,'capture','thermal_2200',293.6,0.5,'m',NULL)")
    v, _, _ = checks.evaluate(con, claim)
    assert v == pytest.approx(0.6 * 0.2 + 0.4 * 0.5)


# ---------- manual CSV ingest ----------

def test_manual_ingest_keeps_good_rows_and_rejects_bad(con, tmp_path):
    d = tmp_path / "manual"
    d.mkdir()
    (d / "al.csv").write_text(
        "# comment line\n"
        "material,quantity,value,unc,unc_kind,unit,T_K,P_Pa,phase,conditions,source_id,locator,method,entered_by,notes\n"
        "Al,density,2.375,0.01,1sigma,g/cm**3,933.5,,l,,literature,doi:10.1/x,measured,test,\n"
        "Al,density,2.3,,,g/cm**3,1000,,l,,literature,,measured,test,missing locator\n"
        "Al,colour,1,,,m,,,,,literature,p.1,,,unknown quantity\n"
    )
    n = manual.ingest(con, d, log=lambda *_: None)
    assert n == 1
    row = con.execute("SELECT value_si, unit_si, source_id FROM property").fetchone()
    assert row["value_si"] == pytest.approx(2375) and row["source_id"] == "literature"
    msg = con.execute("SELECT message FROM ingest_run WHERE ingester='manual'").fetchone()[0]
    assert msg.startswith("2 rejected")


# ---------- network layer: cache and remote zip over a local HTTP server ----------

class _RangeHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send_head(self):
        path = self.translate_path(self.path)
        data = open(path, "rb").read()
        rng = self.headers.get("Range")
        if rng:
            a, b = rng.split("=")[1].split("-")
            a, b = int(a), int(b) if b else len(data) - 1
            self.send_response(206)
            body = data[a:b + 1]
        else:
            self.send_response(200)
            body = data
        self.send_header("Content-Length", str(len(body) if self.command == "GET" else len(data)))
        self.end_headers()
        return io.BytesIO(body)


@pytest.fixture
def server(tmp_path):
    site = tmp_path / "site"
    site.mkdir()
    with zipfile.ZipFile(site / "lib.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("neutrons/n-013_Al_027.endf", "AL27 EVALUATION " * 500)
        z.writestr("neutrons/n-011_Na_023.endf", "NA23 EVALUATION " * 500)
    (site / "data.csv").write_text("a,b\n1,2\n")
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_RangeHandler, directory=str(site)))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def test_fetch_caches_and_records_provenance(con, server, monkeypatch):
    monkeypatch.setattr(fetch._session, "trust_env", False)  # bypass the agent proxy for localhost
    aid1, p1 = fetch.fetch(con, "literature", f"{server}/data.csv")
    aid2, p2 = fetch.fetch(con, "literature", f"{server}/data.csv")
    assert aid1 == aid2 and p1 == p2 and p1.read_text() == "a,b\n1,2\n"
    art = con.execute("SELECT sha256, bytes FROM artifact WHERE artifact_id=?", (aid1,)).fetchone()
    assert art["bytes"] == 8 and len(art["sha256"]) == 64


def test_remote_zip_reads_one_member_with_ranges(con, server, monkeypatch):
    monkeypatch.setattr(fetch._session, "trust_env", False)
    rz = fetch.RemoteZip(f"{server}/lib.zip")
    assert "neutrons/n-013_Al_027.endf" in rz.names()
    aid, path = fetch.fetch_member(con, "endfb80", rz, "neutrons/n-013_Al_027.endf")
    assert path.read_text().startswith("AL27 EVALUATION")
    assert con.execute("SELECT member FROM artifact WHERE artifact_id=?", (aid,)).fetchone()[0].endswith("Al_027.endf")

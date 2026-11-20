"""Check figures stated in the design doc (config/claims.yaml) against the database."""
from __future__ import annotations

import csv
import math
import sqlite3
from pathlib import Path

import yaml

from . import thermo
from .chem import Z_OF, parse_formula
from .db import ROOT, utcnow

CLAIMS_YAML = ROOT / "config" / "claims.yaml"
TIME_S = {"s": 1, "min": 60, "h": 3600, "day": 86400, "year": 365.2422 * 86400}


def _nuclide(con, label):
    el, a = label.split("-")
    return con.execute("SELECT * FROM nuclide WHERE z=? AND a=?", (Z_OF[el], int(a))).fetchone()


def _xi(A: float) -> float:
    alpha = ((A - 1) / (A + 1)) ** 2
    return 1 + alpha * math.log(alpha) / (1 - alpha)


def evaluate(con: sqlite3.Connection, c: dict) -> tuple[float | None, str, str]:
    """Return (database value in the claim's unit, unit, basis)."""
    k = c["kind"]
    if k == "half_life":
        n = _nuclide(con, c["nuclide"])
        if not n or n["half_life_s"] is None:
            return None, c["unit"], "nuclide or half-life not in database"
        return n["half_life_s"] / TIME_S[c["unit"]], c["unit"], f"IAEA LiveChart ({n['half_life_text']})"
    if k == "abundance":
        n = _nuclide(con, c["nuclide"])
        return (n["abundance_pct"] if n else None), "%", "IAEA LiveChart"
    if k == "xs_element":
        r = con.execute(
            "SELECT value_b, coverage_pct FROM v_xs_natural WHERE symbol=? AND mt=? AND weighting_id=?",
            (c["element"], c["mt"], c["weighting"]),
        ).fetchone()
        if not r:
            return None, "b", "isotopes not processed yet"
        if r["coverage_pct"] < 99.9:
            return None, "b", f"only {r['coverage_pct']:.2f}% of natural abundance processed"
        return r["value_b"], "b", f"ENDF/B-VIII.0, abundance-weighted isotopes, {c['weighting']}"
    if k == "xi":
        rs = con.execute(
            "SELECT abundance_pct, atomic_mass_uu FROM nuclide WHERE z=? AND abundance_pct > 0", (Z_OF[c["element"]],)
        ).fetchall()
        if not rs:
            return None, "", "no isotopes"
        A = sum(r["abundance_pct"] * r["atomic_mass_uu"] for r in rs) / sum(r["abundance_pct"] for r in rs) / 1e6
        return _xi(A), "", f"1 + a ln a/(1-a), a = ((A-1)/(A+1))^2, mean A = {A:.3f} from LiveChart masses (free-atom, elastic only)"
    if k == "dfG_per_O2":
        sid = thermo.find_species(con, c["formula"], c["phase"])
        if sid is None:
            return None, "kJ/mol O2", "species not in NIST-JANAF"
        g = thermo.interp(con, sid, "dfG", c["T_K"])
        n_o = parse_formula(c["formula"]).get("O", 0)
        return abs(g) / (n_o / 2), "kJ/mol O2", f"NIST-JANAF dfG at {c['T_K']} K / (n_O/2)"
    if k in ("melting_point", "boiling_point"):
        fn = thermo.melting_point_K if k == "melting_point" else thermo.boiling_point_K
        T, basis = fn(con, c["formula"])
        if T is None and k == "melting_point":
            r = con.execute("SELECT value_si FROM property WHERE material=? AND quantity='melting_point' AND source_id='sgte_unary' "
                            "ORDER BY property_id DESC LIMIT 1", (c["formula"],)).fetchone()
            if r:
                T, basis = r[0], "SGTE unary (G_liquid = G_solid, pycalphad)"
        return (None if T is None else T - 273.15), "degC", basis
    if k == "vapor_pressure":
        p, basis = thermo.vapor_pressure_bar(con, c["formula"], c["T_C"] + 273.15)
        return p, "bar", basis
    if k == "cp_mass":
        sid = thermo.find_species(con, c["formula"], c["phase"])
        if sid is None:
            return None, "kJ/(kg K)", "species not in NIST-JANAF"
        cp = thermo.interp(con, sid, "cp", c["T_C"] + 273.15)
        rs = con.execute(
            "SELECT abundance_pct, atomic_mass_uu FROM nuclide WHERE z=? AND abundance_pct > 0",
            (Z_OF[c["formula"]],),
        ).fetchall()
        M = sum(r["abundance_pct"] * r["atomic_mass_uu"] for r in rs) / sum(r["abundance_pct"] for r in rs) / 1e6
        return (None if cp is None else cp / M), "kJ/(kg K)", "NIST-JANAF Cp / molar mass from LiveChart"
    raise ValueError(f"unknown claim kind {k}")


def run(con: sqlite3.Connection, out_dir: Path = ROOT / "reports") -> list[dict]:
    claims = yaml.safe_load(CLAIMS_YAML.read_text())["claims"]
    results = []
    for c in claims:
        c["value"] = float(c["value"])  # YAML 1.1 reads e.g. 7.2e5 as a string
        db_value, unit, basis = evaluate(con, c)
        tol = c.get("tol", 0.10)
        if db_value is None:
            status, rel = "NOT CHECKED", None
        else:
            rel = (c["value"] - db_value) / db_value if db_value else math.inf
            status = "CONFIRMED" if abs(rel) <= tol else "DIFFERS"
        label = c.get("nuclide") or c.get("element") or c.get("formula")
        cond = f" at {c['T_C']} degC" if "T_C" in c else (f" at {c['T_K']} K" if "T_K" in c else "")
        results.append({
            "status": status, "kind": c["kind"], "item": f"{label}{cond}", "doc_value": c["value"],
            "db_value": None if db_value is None else float(f"{db_value:.4g}"), "unit": unit,
            "rel_diff_pct": None if rel is None else round(100 * rel, 1), "tolerance_pct": round(100 * tol, 1),
            "basis": basis, "where_in_doc": c.get("where", ""),
        })

    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "claims_check.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(results[0]))
        w.writeheader()
        w.writerows(results)
    counts = {s: sum(r["status"] == s for r in results) for s in ("CONFIRMED", "DIFFERS", "NOT CHECKED")}
    lines = [
        "# Claims check", "",
        f"Generated {utcnow()}. {counts['CONFIRMED']} confirmed, {counts['DIFFERS']} differ, "
        f"{counts['NOT CHECKED']} not checkable yet.", "",
        "| Status | Item | Doc value | Database value | Unit | Diff % | Basis | Where in doc |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    order = {"DIFFERS": 0, "NOT CHECKED": 1, "CONFIRMED": 2}
    for r in sorted(results, key=lambda r: order[r["status"]]):
        lines.append(
            f"| {r['status']} | {r['kind']}: {r['item']} | {r['doc_value']} | {'' if r['db_value'] is None else r['db_value']} | "
            f"{r['unit']} | {'' if r['rel_diff_pct'] is None else r['rel_diff_pct']} | {r['basis']} | {r['where_in_doc']} |"
        )
    (out_dir / "claims_check.md").write_text("\n".join(lines) + "\n")
    return results

"""Hand-entered values from handbooks and papers (data/manual/*.csv).

Each row must name a registered source and a locator (page, table, equation or DOI),
and give a unit that pint understands. Values are stored as published and in SI.
Rows that fail validation are reported and skipped; nothing is guessed.
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

import pint
import yaml

from ..db import ROOT, ingest_run, utcnow

MANUAL_DIR = ROOT / "data" / "manual"
QUANTITIES = ROOT / "config" / "quantities.yaml"
REQUIRED = ("material", "quantity", "value", "unit", "source_id", "locator")
UREG = pint.UnitRegistry()
UREG.define("ppm = 1e-6 = _ppm")


def _float(x: str | None) -> float | None:
    x = (x or "").strip()
    return float(x) if x else None


def validate_row(row: dict, quantities: dict, sources: set[str]) -> dict:
    for f in REQUIRED:
        if not (row.get(f) or "").strip():
            raise ValueError(f"missing {f}")
    q = row["quantity"].strip()
    if q not in quantities:
        raise ValueError(f"unknown quantity {q!r} (add it to config/quantities.yaml)")
    if row["source_id"] not in sources:
        raise ValueError(f"unregistered source {row['source_id']!r}")
    unit_si = quantities[q]
    value = float(row["value"])
    value_si = UREG.Quantity(value, row["unit"].strip()).to(unit_si).magnitude  # pint handles degC offsets
    unc = _float(row.get("unc"))
    T = _float(row.get("T_K"))
    return {
        "material": row["material"].strip(), "quantity": q, "value": value, "unc": unc,
        "unc_kind": (row.get("unc_kind") or ("none" if unc is None else "stated")).strip(),
        "unit": row["unit"].strip(), "value_si": value_si, "unit_si": unit_si, "T_K": T,
        "P_Pa": _float(row.get("P_Pa")), "phase": (row.get("phase") or "").strip() or None,
        "conditions": (row.get("conditions") or "").strip() or None, "source_id": row["source_id"].strip(),
        "locator": row["locator"].strip(), "method": (row.get("method") or "").strip() or None,
        "entered_by": (row.get("entered_by") or "").strip() or None, "entered_at": utcnow(),
        "notes": (row.get("notes") or "").strip() or None,
    }


def ingest(con: sqlite3.Connection, directory: Path = MANUAL_DIR, log=print) -> int:
    quantities = yaml.safe_load(QUANTITIES.read_text())["quantities"]
    sources = {r[0] for r in con.execute("SELECT source_id FROM source")}
    with ingest_run(con, "manual") as info:
        con.execute("DELETE FROM property WHERE artifact_id IS NULL")  # manual rows are rebuilt from the CSVs
        good, bad = [], []
        for path in sorted(directory.glob("*.csv")):
            with path.open(newline="") as fh:
                for i, row in enumerate(csv.DictReader(r for r in fh if not r.startswith("#")), start=2):
                    try:
                        good.append(validate_row(row, quantities, sources))
                    except Exception as exc:
                        bad.append(f"{path.name}:{i}: {exc}")
        con.executemany(
            """INSERT INTO property (material, quantity, value, unc, unc_kind, unit, value_si, unit_si, T_K, P_Pa,
               phase, conditions, source_id, locator, method, entered_by, entered_at, notes)
               VALUES (:material, :quantity, :value, :unc, :unc_kind, :unit, :value_si, :unit_si, :T_K, :P_Pa,
               :phase, :conditions, :source_id, :locator, :method, :entered_by, :entered_at, :notes)""",
            good,
        )
        info["rows"] = len(good)
        info["message"] = f"{len(bad)} rejected" + (": " + " | ".join(bad[:20]) if bad else "")
        for b in bad:
            log("  rejected " + b)
    return len(good)

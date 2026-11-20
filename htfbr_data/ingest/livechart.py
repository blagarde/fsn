"""IAEA LiveChart of Nuclides: ground-state properties for all nuclides."""
from __future__ import annotations

import csv
import io
import json
import sqlite3

from ..db import ingest_run
from ..fetch import fetch

SOURCE_ID = "iaea_livechart"
URL = "https://nds.iaea.org/relnsd/v1/data?fields=ground_states&nuclides=all"


def _num(text: str | None) -> float | None:
    text = (text or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse(text: str) -> list[dict]:
    rows = []
    reader = csv.DictReader(io.StringIO(text))
    reader.fieldnames = [f.strip().lower() for f in reader.fieldnames]
    for r in reader:
        if not r.get("z", "").strip().isdigit():
            continue
        z, n = int(r["z"]), int(r["n"])
        stable = r["half_life"].strip().upper() == "STABLE"
        modes = []
        for i in (1, 2, 3):
            mode = (r.get(f"decay_{i}") or "").strip()
            if mode:
                modes.append({"mode": mode, "pct": _num(r.get(f"decay_{i}_%")), "unc": _num(r.get(f"unc_{i}"))})
        rows.append(
            {
                "z": z,
                "a": z + n,
                "symbol": r["symbol"].strip(),
                "abundance_pct": _num(r["abundance"]),
                "abundance_unc": _num(r["unc_a"]),
                "stable": int(stable),
                "half_life_s": None if stable else _num(r["half_life_sec"]),
                "half_life_unc_s": None if stable else _num(r["unc_hls"]),
                "half_life_text": " ".join(x for x in (r["operator_hl"], r["half_life"], r["unit_hl"]) if x and x.strip()).strip(),
                "decay_modes": json.dumps(modes),
                "spin_parity": r["jp"].strip() or None,
                "atomic_mass_uu": _num(r["atomic_mass"]),
                "atomic_mass_unc": _num(r["unc_am"]),
            }
        )
    return rows


def ingest(con: sqlite3.Connection, refresh: bool = False) -> int:
    with ingest_run(con, "livechart") as info:
        artifact_id, path = fetch(con, SOURCE_ID, URL, refresh=refresh)
        rows = parse(path.read_text(encoding="utf-8"))
        if len(rows) < 3000:
            raise ValueError(f"only {len(rows)} nuclides parsed; expected > 3000")
        for r in rows:
            r["artifact_id"] = artifact_id
        con.executemany(
            """INSERT OR REPLACE INTO nuclide (z, a, symbol, abundance_pct, abundance_unc, stable, half_life_s,
               half_life_unc_s, half_life_text, decay_modes, spin_parity, atomic_mass_uu, atomic_mass_unc, artifact_id)
               VALUES (:z, :a, :symbol, :abundance_pct, :abundance_unc, :stable, :half_life_s, :half_life_unc_s,
               :half_life_text, :decay_modes, :spin_parity, :atomic_mass_uu, :atomic_mass_unc, :artifact_id)""",
            rows,
        )
        info["rows"] = len(rows)
    return len(rows)

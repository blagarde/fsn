"""Load config/sources.yaml into the `source` table."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml

from .db import ROOT

SOURCES_YAML = ROOT / "config" / "sources.yaml"
FIELDS = ("source_id", "name", "publisher", "url", "version", "tier", "kind", "access", "status", "license", "citation", "notes")


def load(con: sqlite3.Connection, path: Path = SOURCES_YAML) -> int:
    entries = yaml.safe_load(path.read_text())["sources"]
    ids = [e["source_id"] for e in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate source_id in sources.yaml")
    for e in entries:
        unknown = set(e) - set(FIELDS)
        if unknown:
            raise ValueError(f"{e['source_id']}: unknown fields {sorted(unknown)}")
        row = {f: e.get(f) for f in FIELDS}
        row["version"] = None if row["version"] is None else str(row["version"])
        con.execute(
            f"""INSERT INTO source ({', '.join(FIELDS)}) VALUES ({', '.join(':' + f for f in FIELDS)})
                ON CONFLICT(source_id) DO UPDATE SET {', '.join(f'{f}=excluded.{f}' for f in FIELDS[1:])}""",
            row,
        )
    con.commit()
    return len(entries)

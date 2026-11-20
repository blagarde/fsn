"""SQLite connection, schema setup and ingest-run bookkeeping."""
from __future__ import annotations

import contextlib
import datetime as dt
import sqlite3
from importlib import resources
from pathlib import Path

from . import __version__

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "data" / "htfbr.sqlite"


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def connect(path: Path | str = DEFAULT_DB) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(resources.files(__package__).joinpath("schema.sql").read_text())
    return con


@contextlib.contextmanager
def ingest_run(con: sqlite3.Connection, ingester: str):
    """Record start/end/status of an ingest; yields a dict the ingester fills with `rows`."""
    cur = con.execute(
        "INSERT INTO ingest_run (ingester, started_at, status, code_version) VALUES (?, ?, 'running', ?)",
        (ingester, utcnow(), __version__),
    )
    run_id, info = cur.lastrowid, {"rows": 0, "message": ""}
    con.commit()
    try:
        yield info
    except Exception as exc:
        con.rollback()
        con.execute(
            "UPDATE ingest_run SET finished_at=?, status='failed', message=? WHERE run_id=?",
            (utcnow(), f"{type(exc).__name__}: {exc}", run_id),
        )
        con.commit()
        raise
    con.execute(
        "UPDATE ingest_run SET finished_at=?, status='ok', rows=?, message=? WHERE run_id=?",
        (utcnow(), info["rows"], info["message"], run_id),
    )
    con.commit()

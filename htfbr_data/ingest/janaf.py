"""NIST-JANAF thermochemical tables.

Index pages (tables/<El>-index.html) list every table that contains an element:
CAS, formula, name, phase and a link. Tables themselves are fetched as .txt.
"""
from __future__ import annotations

import html
import re
import sqlite3

from ..chem import parse_formula
from ..db import ingest_run
from ..fetch import fetch

SOURCE_ID = "nist_janaf"
BASE = "https://janaf.nist.gov/tables/"
_ROW = re.compile(r"<tr>(.*?)</tr>", re.S | re.I)
_CELL = re.compile(r"<td[^>]*>(.*?)</td>", re.S | re.I)
_LINK = re.compile(r'href="([A-Za-z]+-\d+)\.html"')
COLUMNS = ("cp", "s", "gef", "h_rel", "dfH", "dfG", "log_kf")


def parse_index(page: str) -> list[dict]:
    out = []
    for row in _ROW.findall(page):
        cells = _CELL.findall(row)
        link = _LINK.search(row)
        if len(cells) < 4 or not link:
            continue
        text = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in cells]
        out.append({"cas": text[0] or None, "formula": text[1], "name": text[2], "phase": text[3], "table_id": link.group(1)})
    return out


def _value(tok: str) -> float | None:
    return None if tok.upper() == "INFINITE" else float(tok)


def parse_table(text: str) -> tuple[dict, list[dict]]:
    """Return (header, rows). Rows at phase transitions carry a text note in place of later columns."""
    lines = [ln.rstrip("\n") for ln in text.splitlines() if ln.strip()]
    name, _, formula = lines[0].partition("\t")
    if not lines[1].startswith("T(K)"):
        raise ValueError("not a JANAF table: missing T(K) header")
    rows = []
    for i, ln in enumerate(lines[2:]):
        toks = ln.split("\t") if "\t" in ln else ln.split()
        toks = [t.strip() for t in toks if t.strip()]
        try:
            T = float(toks[0])
        except ValueError:
            continue
        row = {"row_index": i, "T_K": T, **{c: None for c in COLUMNS}, "note": None}
        rest = toks[1:]
        for k, col in enumerate(COLUMNS):
            if k >= len(rest):
                break
            try:
                row[col] = _value(rest[k])
            except ValueError:  # text such as "CRYSTAL <--> LIQUID" replaces the remaining columns
                row["note"] = " ".join(rest[k:])
                break
        rows.append(row)
    return {"name": name.strip(), "formula": formula.strip()}, rows


def ingest(con: sqlite3.Connection, elements: list[str], species: list[tuple[str, str]], refresh: bool = False) -> int:
    with ingest_run(con, "janaf") as info:
        catalog: dict[str, dict] = {}
        for el in elements:
            try:
                _, path = fetch(con, SOURCE_ID, f"{BASE}{el}-index.html", refresh=refresh)
            except Exception as exc:  # element without JANAF tables
                info["message"] += f"no index for {el} ({exc}); "
                continue
            for entry in parse_index(path.read_text(encoding="utf-8", errors="replace")):
                catalog.setdefault(entry["table_id"], entry)

        wanted, missing, n = [(parse_formula(f), ph) for f, ph in species], [], 0
        for (counts, phase), (formula, _) in zip(wanted, species):
            hits = [e for e in catalog.values() if e["phase"] == phase and _safe_counts(e["formula"]) == counts]
            if not hits:
                missing.append(f"{formula}({phase})")
                continue
            for e in hits:
                artifact_id, path = fetch(con, SOURCE_ID, f"{BASE}{e['table_id']}.txt", refresh=refresh)
                header, rows = parse_table(path.read_text(encoding="utf-8", errors="replace"))
                con.execute(
                    """INSERT INTO species (formula, phase, name, cas, table_id, artifact_id) VALUES (?,?,?,?,?,?)
                       ON CONFLICT(table_id) DO UPDATE SET artifact_id=excluded.artifact_id""",
                    (e["formula"], phase, header["name"] or e["name"], e["cas"], e["table_id"], artifact_id),
                )
                sid = con.execute("SELECT species_id FROM species WHERE table_id=?", (e["table_id"],)).fetchone()[0]
                con.execute("DELETE FROM thermo WHERE species_id=?", (sid,))
                con.executemany(
                    f"INSERT INTO thermo (species_id, row_index, T_K, {', '.join(COLUMNS)}, note) VALUES "
                    f"(:species_id, :row_index, :T_K, {', '.join(':' + c for c in COLUMNS)}, :note)",
                    [{**r, "species_id": sid} for r in rows],
                )
                n += len(rows)
        con.commit()
        info["rows"] = n
        if missing:
            info["message"] += "not in JANAF: " + ", ".join(missing)
    return n


def _safe_counts(formula: str):
    try:
        return parse_formula(formula)
    except ValueError:
        return None

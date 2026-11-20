"""CALPHAD thermodynamic databases (TDB and ChemSage DAT files).

For each configured file (pinned to a repository commit):
  1. fetch it through the provenance cache (artifact row with URL, SHA-256, retrieval time);
  2. load it with pycalphad; record elements, phases and whether it loads;
  3. record which element systems are *assessed*: those with interaction (excess) parameters,
     not merely listed elements, using pycalphad's parsed parameters;
  4. for the SGTE unary database, compute element melting points (G_liquid = G_solid) as
     derived properties with provenance.

The coverage of the systems the project needs (config/targets.yaml: calphad_systems_needed)
is reported by `coverage()`.
"""
from __future__ import annotations

import itertools
import json
import re
import sqlite3
from pathlib import Path

from ..chem import SYMBOLS
from ..db import ingest_run, utcnow
from ..fetch import fetch

_ELEMENTS = {s.upper(): s for s in SYMBOLS}
_SKIP = {"VA", "/-", "E"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS calphad_db (
    db_id       TEXT PRIMARY KEY,      -- short label from config
    source_id   TEXT NOT NULL REFERENCES source (source_id),
    path        TEXT NOT NULL,         -- path inside the repository
    artifact_id INTEGER REFERENCES artifact (artifact_id),
    format      TEXT NOT NULL,         -- tdb | dat
    loads_ok    INTEGER NOT NULL,
    load_error  TEXT,
    elements    TEXT,                  -- JSON list
    phases      TEXT,                  -- JSON list
    header      TEXT,                  -- leading comment lines (citation info when present)
    note        TEXT
);
CREATE TABLE IF NOT EXISTS calphad_system (
    db_id   TEXT NOT NULL REFERENCES calphad_db (db_id),
    system  TEXT NOT NULL,             -- sorted element symbols joined by '-', e.g. Al-Zr
    order_n INTEGER NOT NULL,          -- 2 binary, 3 ternary
    phases  TEXT NOT NULL,             -- JSON list of phases carrying interaction parameters
    liquid  INTEGER NOT NULL,          -- 1 if the liquid phase is assessed for this system
    PRIMARY KEY (db_id, system)
);
"""


def _elements_of_species(sp) -> set[str]:
    out = set()
    for name in getattr(sp, "constituents", {}) or {}:
        el = _ELEMENTS.get(str(name).upper())
        if el and el.upper() not in _SKIP:
            out.add(el)
    if not out:  # species without a constituents dict: parse its name
        for tok in re.findall(r"[A-Z][a-z]?", str(getattr(sp, "name", sp)).title()):
            el = _ELEMENTS.get(tok.upper())
            if el and tok.upper() not in _SKIP:
                out.add(el)
    return out


def assessed_systems(dbf) -> dict[str, dict]:
    """System -> {'phases': set, 'liquid': bool}.

    A system counts as assessed when some condensed-phase parameter spans two or more of its
    elements: an interaction (excess) term, written L(...) or, in older files, G(...) with
    several species in one sublattice; or a compound end-member with different elements on
    different sublattices. Gas-phase species are ignored (they say nothing about condensed phases).
    """
    systems: dict[str, dict] = {}
    for p in dbf._parameters.all():
        phase = str(p.get("phase_name", ""))
        if phase.upper().startswith("GAS"):
            continue
        els: set[str] = set()
        for sublattice in p.get("constituent_array", ()):
            for sp in sublattice:
                els |= _elements_of_species(sp)
        if len(els) < 2:
            continue
        for n in (2, 3):
            for combo in itertools.combinations(sorted(els), n):
                entry = systems.setdefault("-".join(combo), {"phases": set(), "liquid": False})
                entry["phases"].add(phase)
                entry["liquid"] |= phase.upper().startswith(("LIQ", "IONIC_LIQ"))
    return systems


def dedupe_parameters(dbf, remove: bool = True) -> tuple[int, int]:
    """Remove repeated parameters (same type, phase, constituents, order). pycalphad sums duplicates,
    which silently doubles a Gibbs energy. Returns (identical duplicates, conflicting duplicates);
    the first occurrence is kept in both cases."""
    seen: dict[tuple, str] = {}
    drop, conflicts = [], 0
    for doc in dbf._parameters.all():
        key = (doc.get("parameter_type"), doc.get("phase_name"), str(doc.get("constituent_array")),
               doc.get("parameter_order"), str(doc.get("diffusing_species")))
        expr = str(doc.get("parameter"))
        if key in seen:
            drop.append(doc.doc_id)
            conflicts += seen[key] != expr
        else:
            seen[key] = expr
    if drop and remove:
        dbf._parameters.remove(doc_ids=drop)
    return len(drop) - conflicts, conflicts


def _header(text: str, n: int = 25) -> str:
    lines = [ln.strip() for ln in text.splitlines()[:200] if ln.strip().startswith("$") or "REFERENCE" in ln.upper()]
    return "\n".join(lines[:n])


def melting_points(dbf, elements: list[str]) -> dict[str, float]:
    """Element melting points from a unary database: T where G(liquid) equals the lowest solid G (1 bar)."""
    import numpy as np
    from pycalphad import calculate

    T = np.arange(250.0, 4500.0, 0.5)
    out = {}
    for el in elements:
        sym = el.upper()
        phases = [ph for ph, obj in dbf.phases.items() if not ph.upper().startswith("GAS")
                  and any(sym in {str(c).upper() for sp in sub for c in (getattr(sp, "constituents", None) or {getattr(sp, "name", sp): 1})} for sub in (obj.constituents or ()))]
        if "LIQUID" not in phases:
            continue
        gm = {}
        for ph in phases:
            try:
                res = calculate(dbf, [sym, "VA"], ph, T=T, P=101325, N=1, output="GM", pdens=1)
                gm[ph] = np.nanmin(res.GM.values.reshape(len(T), -1), axis=1)
            except Exception:
                continue
        solids = [g for ph, g in gm.items() if ph != "LIQUID"]
        if "LIQUID" not in gm or not solids:
            continue
        diff = gm["LIQUID"] - np.nanmin(np.vstack(solids), axis=0)   # > 0 while solid is stable
        idx = np.where((diff[:-1] > 0) & (diff[1:] <= 0))[0]
        if len(idx):
            i = idx[0]
            out[el] = round(float(T[i] + (T[i + 1] - T[i]) * diff[i] / (diff[i] - diff[i + 1])), 2)
    return out


def ingest(con: sqlite3.Connection, files: list[dict], refresh: bool = False, unary_elements: list[str] | None = None,
           log=print) -> int:
    from pycalphad import Database

    con.executescript(SCHEMA)
    with ingest_run(con, "calphad") as info:
        n_sys, failed = 0, []
        for f in files:
            url = f"https://raw.githubusercontent.com/{f['repo']}/{f['commit']}/{f['path']}"
            artifact_id, path = fetch(con, f["source_id"], url, refresh=refresh)
            text = Path(path).read_text(errors="replace")
            fmt = "dat" if f["path"].lower().endswith(".dat") else "tdb"
            loads_ok, err, dbf = 1, None, None
            try:
                dbf = Database(str(path))  # format detected from the file extension
            except Exception as exc:
                loads_ok, err = 0, f"{type(exc).__name__}: {str(exc)[:300]}"
                failed.append(f["db_id"])
            note = f.get("note") or ""
            if dbf is not None:
                # In TDB files a repeated parameter is always an error (pycalphad would sum it), so drop repeats.
                # In ChemSage DAT files repeats can be legitimate model terms: report only.
                same, conflict = dedupe_parameters(dbf, remove=(fmt == "tdb"))
                if same or conflict:
                    verb = "removed" if fmt == "tdb" else "found (kept, DAT format)"
                    note = (note + f" | {verb} {same} identical and {conflict} differing repeated parameter(s)").strip(" |")
                    log(f"  {f['db_id']}: {verb} {same} identical, {conflict} differing repeated parameter(s)")
            elements = sorted(_ELEMENTS[e.upper()] for e in (dbf.elements if dbf else []) if e.upper() in _ELEMENTS and e.upper() not in _SKIP)
            con.execute(
                "INSERT OR REPLACE INTO calphad_db VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (f["db_id"], f["source_id"], f["path"], artifact_id, fmt, loads_ok, err, json.dumps(elements),
                 json.dumps(sorted(dbf.phases)) if dbf else None, _header(text), note),
            )
            con.execute("DELETE FROM calphad_system WHERE db_id=?", (f["db_id"],))
            if dbf is not None:
                rows = [(f["db_id"], s, s.count("-") + 1, json.dumps(sorted(d["phases"])), int(d["liquid"]))
                        for s, d in assessed_systems(dbf).items()]
                con.executemany("INSERT INTO calphad_system VALUES (?,?,?,?,?)", rows)
                n_sys += len(rows)
            log(f"  {f['db_id']}: {'ok' if loads_ok else 'FAILED to load'}, {len(elements)} elements")

            if dbf is not None and f.get("unary") and unary_elements:
                mps = melting_points(dbf, unary_elements)
                con.execute("DELETE FROM property WHERE source_id=? AND quantity='melting_point' AND artifact_id=?",
                            (f["source_id"], artifact_id))
                con.executemany(
                    """INSERT INTO property (material, quantity, value, unc, unc_kind, unit, value_si, unit_si, T_K, P_Pa,
                       phase, conditions, source_id, locator, method, artifact_id, entered_by, entered_at, notes)
                       VALUES (?, 'melting_point', ?, NULL, 'none', 'kelvin', ?, 'kelvin', NULL, 101325, NULL, NULL, ?, ?,
                       'calculated', ?, 'htfbr-data calphad', ?, 'G(liquid) = G(stable solid), pycalphad equilibrium')""",
                    [(el, T, T, f["source_id"], f"{f['path']} @ {f['commit'][:12]}", artifact_id, utcnow()) for el, T in mps.items()],
                )
                log(f"  {f['db_id']}: melting points for {len(mps)} elements")
        con.commit()
        info["rows"] = n_sys
        info["message"] = f"failed to load: {', '.join(failed)}" if failed else ""
    return n_sys


def coverage(con: sqlite3.Connection, needed: list[dict]) -> list[dict]:
    """For each needed system: databases that assess it (all binaries for a ternary), or the gap."""
    con.executescript(SCHEMA)
    out = []
    for item in needed:
        els = sorted(item["system"].split("-"))
        key = "-".join(els)
        direct = con.execute(
            "SELECT s.db_id, s.liquid FROM calphad_system s JOIN calphad_db d USING (db_id) WHERE s.system=? AND d.loads_ok=1",
            (key,)).fetchall()
        binaries = {}
        if len(els) == 3:
            for a, b in itertools.combinations(els, 2):
                binaries[f"{a}-{b}"] = [r[0] for r in con.execute(
                    "SELECT db_id FROM calphad_system WHERE system=?", (f"{a}-{b}",))]
        extrapolable = []
        if len(els) == 3 and binaries:
            common = set.intersection(*(set(v) for v in binaries.values()))
            extrapolable = sorted(common)
        out.append({
            "system": key, "why": item.get("why", ""), "questions": item.get("questions", []),
            "databases": sorted({r[0] for r in direct}), "liquid": any(r[1] for r in direct),
            "binaries": binaries, "extrapolable": extrapolable,
        })
    return out

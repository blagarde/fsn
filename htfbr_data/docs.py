"""Generate and validate the project documentation in docs/.

- designs/README.md and materials/README.md index tables are built from page front matter.
- Material pages get two generated blocks: `db-facts` (from the property database, when available)
  and `used-by` (designs whose front matter lists the material).
- docs/data/claims-check.md is copied from reports/claims_check.md.
- validate() checks front matter, cross-references (materials, questions, studies) and relative links.

Generated text sits between `<!-- BEGIN GENERATED <name> -->` and `<!-- END GENERATED -->`.
"""
from __future__ import annotations

import math
import re
import sqlite3
from pathlib import Path

import yaml

from . import thermo
from .chem import Z_OF, parse_formula
from .db import ROOT

DOCS = ROOT / "docs"
DESIGN_KEYS = ("id", "title", "family", "designation", "status", "outlet_C", "fuel", "coolant", "boundary",
               "key_risk", "materials", "studies", "questions", "updated")
MATERIAL_KEYS = ("id", "title", "formula", "kind", "roles", "status", "updated")
DESIGN_STATUS = ("seed", "exploring", "analysed", "parked", "rejected")
MATERIAL_STATUS = ("candidate", "shortlisted", "excluded")
_FM = re.compile(r"\A---\n(.*?)\n---\n", re.S)
_BLOCK = r"(<!-- BEGIN GENERATED {name} -->\n)(.*?)(<!-- END GENERATED -->)"


# ---------- reading pages ----------

def read_page(path: Path) -> tuple[dict, str]:
    text = path.read_text()
    m = _FM.match(text)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, text[m.end():]


def pages(folder: str) -> list[tuple[Path, dict]]:
    out = []
    for p in sorted((DOCS / folder).glob("*.md")):
        if p.name.startswith("_") or p.name == "README.md":
            continue
        meta, _ = read_page(p)
        out.append((p, meta))
    return out


def _id_sort(meta: dict):
    m = re.match(r"([A-Z]+)(\d+)", str(meta.get("id", "")))
    return (m.group(1), int(m.group(2))) if m else (str(meta.get("id")), 0)


def replace_block(text: str, name: str, content: str) -> str:
    pattern = re.compile(_BLOCK.format(name=re.escape(name)), re.S)
    if not pattern.search(text):
        raise ValueError(f"missing generated block {name!r}")
    return pattern.sub(lambda m: m.group(1) + content.rstrip() + "\n" + m.group(3), text, count=1)


# ---------- indexes ----------

def _cell(v) -> str:
    if isinstance(v, list):
        v = ", ".join(map(str, v))
    return str(v if v is not None else "").replace("|", "\\|").replace("\n", " ")


def design_index() -> str:
    designs = sorted(pages("designs"), key=lambda pm: _id_sort(pm[1]))
    counts = {s: sum(m.get("status") == s for _, m in designs) for s in DESIGN_STATUS}
    lines = [
        f"{len(designs)} designs: " + ", ".join(f"{n} {s}" for s, n in counts.items() if n) + ".", "",
        "| ID | Design | Status | Outlet (°C) | Fuel | Coolant | Boundary | Key risk | Designation |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for p, m in designs:
        lines.append(f"| [{m['id']}]({p.name}) | {_cell(m['title'])} | {m['status']} | {_cell(m['outlet_C'])} | "
                     f"{_cell(m['fuel'])} | {_cell(m['coolant'])} | {_cell(m['boundary'])} | {_cell(m['key_risk'])} | "
                     f"`{_cell(m['designation'])}` |")
    families: dict[str, list[str]] = {}
    for p, m in designs:
        families.setdefault(m["family"], []).append(f"[{m['id']}]({p.name})")
    lines += ["", "**By family:** " + " · ".join(f"{fam}: {', '.join(ids)}" for fam, ids in families.items())]
    return "\n".join(lines)


def used_by() -> dict[str, list[tuple[str, str, str]]]:
    out: dict[str, list[tuple[str, str, str]]] = {}
    for p, m in sorted(pages("designs"), key=lambda pm: _id_sort(pm[1])):
        for slug in m.get("materials") or []:
            out.setdefault(slug, []).append((m["id"], p.name, m["title"]))
    return out


def material_index() -> str:
    mats = pages("materials")
    users = used_by()
    lines = [
        f"{len(mats)} materials with pages.", "",
        "| Material | Formula | Roles | Status | Used by designs |",
        "| --- | --- | --- | --- | --- |",
    ]
    for p, m in sorted(mats, key=lambda pm: pm[1]["title"].lower()):
        ds = ", ".join(f"[{i}](../designs/{f})" for i, f, _ in users.get(m["id"], [])) or "—"
        lines.append(f"| [{_cell(m['title'])}]({p.name}) | {m['formula']} | {_cell(m['roles'])} | {m['status']} | {ds} |")
    by_role: dict[str, list[str]] = {}
    for p, m in mats:
        for r in m.get("roles") or []:
            by_role.setdefault(r, []).append(f"[{m['title']}]({p.name})")
    lines += ["", "**By role:** " + " · ".join(f"{r}: {', '.join(sorted(v))}" for r, v in sorted(by_role.items()))]
    return "\n".join(lines)


# ---------- database facts ----------

def _fmt(x: float, digits: int = 3) -> str:
    if x == 0:
        return "0"
    if abs(x) >= 1000:
        return f"{x:,.0f}"
    return f"{x:.{digits}g}"


def db_facts(con: sqlite3.Connection, meta: dict) -> str:
    formula, rows = meta["formula"], []
    counts = parse_formula(formula)
    is_element = len(counts) == 1 and list(counts.values())[0] == 1

    if is_element:
        z = Z_OF[formula]
        iso = con.execute("SELECT symbol, a, abundance_pct FROM nuclide WHERE z=? AND abundance_pct > 0 ORDER BY a", (z,)).fetchall()
        if iso:
            rows.append(("Natural isotopes", ", ".join(f"{r['symbol']}-{r['a']} ({_fmt(r['abundance_pct'])}%)" for r in iso), "IAEA LiveChart"))
        for mt, label in ((102, "Capture"), (101, "Absorption (non-fission)")):
            for wid, wlabel in (("thermal_2200", "at 0.0253 eV"), ("watt_u235", "U-235 fission-spectrum average")):
                r = con.execute("SELECT value_b, coverage_pct FROM v_xs_natural WHERE z=? AND mt=? AND weighting_id=?", (z, mt, wid)).fetchone()
                if r and r["coverage_pct"] > 99.9:
                    v = r["value_b"]
                    val = f"{_fmt(v)} b" if v >= 1 or wid == "thermal_2200" else f"{_fmt(1000 * v)} mb"
                    rows.append((f"{label}, {wlabel}", val, "ENDF/B-VIII.0 via NJOY2016, natural abundances"))
        if iso:
            masses = con.execute("SELECT abundance_pct, atomic_mass_uu FROM nuclide WHERE z=? AND abundance_pct > 0", (z,)).fetchall()
            A = sum(r["abundance_pct"] * r["atomic_mass_uu"] for r in masses) / sum(r["abundance_pct"] for r in masses) / 1e6
            alpha = ((A - 1) / (A + 1)) ** 2
            xi = 1 + alpha * math.log(alpha) / (1 - alpha) if A > 1.01 else 1.0
            rows.append(("Moderating parameter ξ", _fmt(xi), f"computed from mean atomic mass {A:.3f} u (LiveChart)"))

    T, basis = thermo.melting_point_K(con, formula)
    if T:
        rows.append(("Melting point", f"{T - 273.15:,.0f} °C", f"NIST-JANAF ({basis.split(':')[-1].strip()})"))
    T, basis = thermo.boiling_point_K(con, formula)
    if T:
        rows.append(("Boiling point (1 bar)", f"{T - 273.15:,.0f} °C", "NIST-JANAF"))
    for tc in (1500, 2000):
        p, basis = thermo.vapor_pressure_bar(con, formula, tc + 273.15)
        if p is not None:
            src = "NIST-JANAF" + (", Clausius–Clapeyron extrapolation above Tb" if basis.startswith("EXTRAPOLATED") else "")
            rows.append((f"Vapour pressure at {tc:,} °C", f"{_fmt(p)} bar", src))
    if not is_element:
        sid = thermo.find_species(con, formula, "cr") or thermo.find_species(con, formula, "cr,l")
        if sid:
            n_o = counts.get("O", 0)
            for tk in (298.15, 1500.0, 2000.0):
                g = thermo.interp(con, sid, "dfG", tk)
                if g is None:
                    continue
                txt = f"{g:,.0f} kJ/mol" + (f" ({abs(g) / (n_o / 2):,.0f} per mol O2)" if n_o else "")
                rows.append((f"ΔfG° at {tk:,.0f} K", txt, "NIST-JANAF"))
    if not rows:
        return "_Not in the property database yet (see [Q-012](../open-questions.md))._"
    lines = ["| Property | Value | Source |", "| --- | --- | --- |"]
    lines += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    return "\n".join(lines)


# ---------- generation ----------

def generate(con: sqlite3.Connection | None = None, check: bool = False) -> list[str]:
    """Rewrite generated content. Returns the list of files that changed (or would change, with check=True)."""
    changed = []

    def write(path: Path, text: str):
        if path.exists() and path.read_text() == text:
            return
        changed.append(str(path.relative_to(ROOT)))
        if not check:
            path.write_text(text)

    idx = DOCS / "designs" / "README.md"
    write(idx, replace_block(idx.read_text(), "design-index", design_index()))
    idx = DOCS / "materials" / "README.md"
    write(idx, replace_block(idx.read_text(), "material-index", material_index()))

    users = used_by()
    for p, m in pages("materials"):
        text = p.read_text()
        ds = users.get(m["id"], [])
        text = replace_block(text, "used-by", "\n".join(f"- [{i}](../designs/{f}): {t}" for i, f, t in ds) or "_None yet._")
        if con is not None:
            text = replace_block(text, "db-facts", db_facts(con, m))
        write(p, text)

    if con is not None:
        page = calphad_coverage_page(con)
        if page:
            write(DOCS / "data" / "calphad-coverage.md", page)

    report = ROOT / "reports" / "claims_check.md"
    if report.exists():
        body = report.read_text().replace("# Claims check", "# Claims check: doc figures vs property database", 1)
        header = ("<!-- Generated by `htfbr-data check` + `htfbr-data docs`; do not edit. Claims live in config/claims.yaml. -->\n")
        write(DOCS / "data" / "claims-check.md", header + body)
    return changed


# ---------- CALPHAD coverage ----------

def calphad_coverage_page(con: sqlite3.Connection) -> str | None:
    from .ingest import calphad

    if not con.execute("SELECT name FROM sqlite_master WHERE name='calphad_db'").fetchone():
        return None
    targets = yaml.safe_load((ROOT / "config" / "targets.yaml").read_text())
    cov = calphad.coverage(con, targets.get("calphad_systems_needed", []))
    dbs = con.execute(
        "SELECT d.db_id, d.source_id, d.path, d.loads_ok, d.load_error, d.elements, d.note, s.tier, "
        "(SELECT COUNT(*) FROM calphad_system c WHERE c.db_id = d.db_id) n FROM calphad_db d JOIN source s USING (source_id) ORDER BY d.db_id"
    ).fetchall()
    have = [c for c in cov if c["databases"]]
    lines = [
        "<!-- Generated by `htfbr-data calphad` + `htfbr-data docs`; do not edit. Needed systems: config/targets.yaml. -->",
        "# CALPHAD coverage", "",
        f"{len(have)} of {len(cov)} systems the project needs have at least one assessed database loaded. "
        "A system counts as assessed when a condensed-phase parameter spans its elements (interaction term or compound), "
        "not merely when the elements are listed. Each database is graded: full (liquid and compounds), liquid, compounds, or "
        "partial (terminal solid solutions only, which does not count as coverage). A ternary with all three binaries covered in one database can be extrapolated "
        "(standard CALPHAD practice) but has no ternary terms. Coverage does not mean quality: check each database's tier and header.", "",
        "## Needed systems", "",
        "| System | Why | Questions | Databases | Liquid assessed | Ternary: binaries covered |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for c in sorted(cov, key=lambda c: (bool(c["databases"]), c["system"])):
        qs = ", ".join(f"[{q}](../open-questions.md)" for q in c["questions"]) or ""
        bins = "; ".join(f"{b}: {', '.join(f'{db} ({gr})' for db, gr in v.items()) or '**none**'}" for b, v in c["binaries"].items())
        partial = [db for db, gr in c.get("grades", {}).items() if gr == "partial"]
        dbtxt = (", ".join(f"{db} ({c['grades'][db]})" for db in c["databases"]) if c["databases"]
                 else f"extrapolable from binaries in {', '.join(c['extrapolable'])}" if c.get("extrapolable")
                 else "**gap**" + (f" (solid solutions only in {', '.join(partial)})" if partial else ""))
        lines.append(f"| {c['system']} | {c['why']} | {qs} | {dbtxt} | {'yes' if c['liquid'] else ('—' if not c['databases'] else 'no')} | {bins} |")
    lines += ["", "## Databases loaded", "",
              "| Database | Source (tier) | File | Loads | Elements | Assessed systems | Notes |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    import json as _json
    for d in dbs:
        els = ", ".join(_json.loads(d["elements"] or "[]"))
        if len(els) > 60:
            els = f"{len(_json.loads(d['elements']))} elements"
        status = "yes" if d["loads_ok"] else f"no: {(d['load_error'] or '')[:80]}"
        lines.append(f"| {d['db_id']} | {d['source_id']} ({d['tier']}) | `{d['path']}` | {status} | {els} | {d['n']} | {_cell(d['note'] or '')} |")
    lines += ["", "Gaps are filled from sources not yet reachable or not yet entered: TDBDB, NIMS CPDDB, NIST, ORNL MSTDB-TC, "
              "and TDB files published as paper supplements (see [sources](database.md#sources) and `config/sources.yaml`)."]
    return "\n".join(lines) + "\n"


# ---------- validation ----------

_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")  # links and images


def _slug(heading: str) -> str:
    s = re.sub(r"[^\w\- ]", "", heading.strip().lower())
    return s.replace(" ", "-")


def _anchors(path: Path) -> set[str]:
    return {_slug(m.group(1)) for m in re.finditer(r"^#{1,6} (.+)$", path.read_text(), re.M)}


def validate() -> list[str]:
    errors = []
    question_ids = set(re.findall(r"\| (Q-\d{3}) \|", (DOCS / "open-questions.md").read_text()))
    material_ids = {m.get("id") for _, m in pages("materials")}

    for p, m in pages("designs"):
        missing = [k for k in DESIGN_KEYS if k not in m]
        if missing:
            errors.append(f"{p.name}: missing front matter {missing}")
            continue
        if m["id"] != p.stem:
            errors.append(f"{p.name}: id {m['id']!r} does not match file name")
        if m["status"] not in DESIGN_STATUS:
            errors.append(f"{p.name}: bad status {m['status']!r}")
        if len(str(m["designation"]).split("|")) != 10:
            errors.append(f"{p.name}: designation must have 10 axes")
        for slug in m["materials"] or []:
            if slug not in material_ids:
                errors.append(f"{p.name}: unknown material {slug!r}")
        for q in m["questions"] or []:
            if q not in question_ids:
                errors.append(f"{p.name}: unknown question {q}")
        for s in m["studies"] or []:
            if not (DOCS / s).exists():
                errors.append(f"{p.name}: missing study {s}")

    for p, m in pages("materials"):
        missing = [k for k in MATERIAL_KEYS if k not in m]
        if missing:
            errors.append(f"{p.name}: missing front matter {missing}")
            continue
        if m["id"] != p.stem:
            errors.append(f"{p.name}: id {m['id']!r} does not match file name")
        if m["status"] not in MATERIAL_STATUS:
            errors.append(f"{p.name}: bad status {m['status']!r}")
        try:
            parse_formula(m["formula"])
        except ValueError as exc:
            errors.append(f"{p.name}: {exc}")

    for md in [*DOCS.rglob("*.md"), ROOT / "README.md"]:
        for target in _LINK.findall(md.read_text()):
            if re.match(r"[a-z]+://|mailto:", target):
                continue
            path_part, _, anchor = target.partition("#")
            dest = (md.parent / path_part).resolve() if path_part else md
            if not dest.exists():
                errors.append(f"{md.relative_to(ROOT)}: broken link {target}")
                continue
            if anchor and dest.suffix == ".md" and anchor not in _anchors(dest):
                errors.append(f"{md.relative_to(ROOT)}: missing anchor #{anchor} in {path_part or md.name}")

    # every figure has an editable source and is used by at least one page
    figures, sources = DOCS / "assets" / "figures", ROOT / "tools" / "figures" / "src"
    used = "".join(md.read_text() for md in DOCS.rglob("*.md"))
    for svg in sorted(figures.glob("*.svg")):
        if not (sources / f"{svg.stem}.jsx").exists():
            errors.append(f"docs/assets/figures/{svg.name}: no source tools/figures/src/{svg.stem}.jsx")
        if svg.name not in used:
            errors.append(f"docs/assets/figures/{svg.name}: not used by any page")
    for src in sorted(sources.glob("*.jsx")):
        if not (figures / f"{src.stem}.svg").exists():
            errors.append(f"tools/figures/src/{src.name}: not rendered (run npm run render in tools/figures)")
    return errors

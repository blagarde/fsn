"""Command line: htfbr-data <command>.

  init                 create the database and load the source registry
  livechart            ingest IAEA LiveChart ground states
  janaf                ingest NIST-JANAF tables listed in config/targets.yaml
  endf [--only X ...] [--all] [--skip-done]
                       process ENDF/B-VIII.0 evaluations (needs the conda env with NJOY + OpenMC)
  manual               load data/manual/*.csv
  build                init + livechart + janaf + manual (+ endf unless --no-endf)
  check                compare doc claims with the database -> reports/claims_check.{md,csv}
  status               row counts, last ingest runs, sources by status
  sql "<query>"        run a read-only query
"""
from __future__ import annotations

import argparse
import sys

import yaml

from . import checks, registry
from .db import DEFAULT_DB, ROOT, connect
from .ingest import janaf, livechart, manual

TARGETS = ROOT / "config" / "targets.yaml"


def _targets() -> dict:
    return yaml.safe_load(TARGETS.read_text())


def cmd_init(con, a):
    print(f"sources registered: {registry.load(con)}")


def cmd_livechart(con, a):
    print(f"nuclides: {livechart.ingest(con, refresh=a.refresh)}")


def cmd_janaf(con, a):
    t = _targets()
    n = janaf.ingest(con, t["janaf_elements"], [(s[0], ",".join(s[1:])) for s in t["janaf_species"]], refresh=a.refresh)
    msg = con.execute("SELECT message FROM ingest_run WHERE ingester='janaf' ORDER BY run_id DESC LIMIT 1").fetchone()[0]
    print(f"thermo rows: {n}" + (f"\n  {msg}" if msg else ""))


def cmd_endf(con, a):
    from .ingest import endf_xs  # needs numpy + openmc

    t = _targets()
    n = endf_xs.ingest(con, t["endf_nuclides"], t["endf_reactions"], t["endf_temperature_K"], only=a.only,
                       refresh=a.refresh, all_in_library=getattr(a, "all", False), skip_existing=getattr(a, "skip_done", False))
    print(f"cross-section values: {n}")


def cmd_manual(con, a):
    print(f"manual property rows: {manual.ingest(con)}")


def cmd_build(con, a):
    cmd_init(con, a)
    cmd_livechart(con, a)
    cmd_janaf(con, a)
    cmd_manual(con, a)
    if not a.no_endf:
        cmd_endf(con, a)


def cmd_check(con, a):
    res = checks.run(con)
    for s in ("CONFIRMED", "DIFFERS", "NOT CHECKED"):
        print(f"{s:12s} {sum(r['status'] == s for r in res)}")
    for r in res:
        if r["status"] == "DIFFERS":
            print(f"  DIFFERS  {r['kind']}: {r['item']}: doc {r['doc_value']} vs db {r['db_value']} {r['unit']} ({r['rel_diff_pct']}%)")
    print("report: reports/claims_check.md")


def cmd_status(con, a):
    for tbl in ("source", "artifact", "nuclide", "species", "thermo", "xs_avg", "property"):
        print(f"{tbl:10s} {con.execute(f'SELECT COUNT(*) FROM {tbl}').fetchone()[0]}")
    print("\nlast runs:")
    for r in con.execute("SELECT ingester, status, rows, finished_at, substr(message,1,160) m FROM ingest_run ORDER BY run_id DESC LIMIT 8"):
        print(f"  {r['ingester']:10s} {r['status']:7s} {r['rows'] or 0:>7} {r['finished_at'] or '':25s} {r['m'] or ''}")
    print("\nsources by status:")
    for r in con.execute("SELECT status, group_concat(source_id, ', ') ids FROM source GROUP BY status"):
        print(f"  {r['status']:12s} {r['ids']}")


def cmd_sql(con, a):
    if not a.query.lstrip().lower().startswith(("select", "with", "pragma")):
        sys.exit("only read-only queries")
    cur = con.execute(a.query)
    cols = [d[0] for d in cur.description]
    print("\t".join(cols))
    for row in cur:
        print("\t".join("" if v is None else str(v) for v in row))


def main(argv=None):
    p = argparse.ArgumentParser(prog="htfbr-data", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", default=str(DEFAULT_DB))
    p.add_argument("--refresh", action="store_true", help="re-download instead of using cached raw files")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("init", "livechart", "janaf", "manual", "check", "status"):
        sub.add_parser(name)
    e = sub.add_parser("endf")
    e.add_argument("--only", nargs="*", help="nuclides (Al-27) or elements (W) to process")
    e.add_argument("--all", action="store_true", help="every ground-state evaluation in the library, not just config targets")
    e.add_argument("--skip-done", action="store_true", help="skip nuclides already processed with the current reaction set")
    b = sub.add_parser("build")
    b.add_argument("--no-endf", action="store_true")
    b.add_argument("--only", nargs="*")
    q = sub.add_parser("sql")
    q.add_argument("query")
    a = p.parse_args(argv)
    con = connect(a.db)
    if a.cmd not in ("init", "build"):
        registry.load(con)  # keep the registry in sync with config/sources.yaml
    globals()[f"cmd_{a.cmd}"](con, a)


if __name__ == "__main__":
    main()

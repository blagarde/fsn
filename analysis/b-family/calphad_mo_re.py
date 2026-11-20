"""R10 check for Mo-Re cladding (alternative to Nb-1Zr / Mo in B1, B2, B6): Re solubility in bcc Mo
before sigma/chi forms, from the Mo-Re assessment in the oc-mo-ni-re database (Mathieu 2013, tier C copy).
-> results/calphad_mo_re.json"""
import json
import sqlite3

import numpy as np
from pycalphad import Database, equilibrium, variables as v

from bfam import HERE, ROOT

con = sqlite3.connect(f"file:{ROOT / 'data' / 'htfbr.sqlite'}?mode=ro", uri=True)
path = con.execute("SELECT a.local_path FROM calphad_db d JOIN artifact a USING(artifact_id) "
                   "WHERE d.db_id='oc-mo-ni-re'").fetchone()[0]
db = Database(path)
phases = [p for p in ("BCC_A2", "SIGMA", "CHI", "HCP_A3", "LIQUID") if p in db.phases]
out = {"database": "oc-mo-ni-re (Mo-Re: Mathieu 2013)", "path": path, "phases": phases, "results": {}}
xs = np.round(np.arange(0.20, 0.62, 0.02), 3)
for T in (1300, 1500, 1800, 2100):
    eq = equilibrium(db, ["MO", "RE", "VA"], phases, {v.T: T, v.P: 101325, v.N: 1, v.X("RE"): list(xs)})
    rows = []
    for i, x in enumerate(xs):
        ph = [str(p) for p in np.unique(eq.Phase.values[0, 0, 0, i].ravel()) if str(p)]
        rows.append({"x_Re": float(x), "phases": ph})
    limit = next((r["x_Re"] for r in rows if r["phases"] != ["BCC_A2"]), None)
    out["results"][T] = {"first_x_Re_with_second_phase": limit, "scan": rows}
    print(T, "K: bcc single-phase up to x_Re <", limit)
(HERE / "results" / "calphad_mo_re.json").write_text(json.dumps(out, indent=1))

# Family B (B1-B6) Phase 1 screening

Scripts and results behind [docs/studies/b-family-screening.md](../../docs/studies/b-family-screening.md)
and the "Phase 1 screening (2026-11-20)" sections of docs/designs/B1.md to B6.md.

## Rerun

```bash
export PATH=/opt/mamba/envs/nuc/bin:$PATH
cd analysis/b-family
python db_facts.py            # database facts (JANAF, SGTE, ENDF/B-VIII.0 averages, LiveChart) -> results/db_facts.json
python calphad_mo_re.py       # R10: Re solubility in bcc Mo (oc-mo-ni-re database)      -> results/calphad_mo_re.json
python thermal.py             # 1D thermal sizing and cycle limits                         -> results/thermal.json, cycle.json
python run_neutronics.py B1 B2 B3-C B3-N B4 B4-natCl B5-W B5-W184 B5-W186 B5-Mo B6   # -> results/neutronics_<case>.json
python summarize.py           # -> results/summary.json, summary.csv
```

`run_neutronics.py` is resumable: each step is written to `results/neutronics_<case>.partial.json`
as it finishes, and a rerun skips steps already there. Delete the partial file to start a case afresh.
Neutronics needs `data/openmc/cross_sections.xml` (ENDF/B-VIII.0 at 1,200 and 2,100 K; B-10 absent).
Each case takes 20-60 min on one thread.

## Files

| File | Content |
| --- | --- |
| `bfam.py` | Materials (fuel, coolants, claddings, isotope vectors) and `screen_plus()`, a copy of `analysis/common/infinite.screen()` with extra tallies (tritium, (n,p), (n,a), capture per fission) |
| `designs.py` | Homogenised compositions (volume fractions, densities) and isotope variants per case |
| `run_neutronics.py` | Pu-fraction scan (3 points, 10,000 x 40 batches), quadratic fit to k_inf = 1.15, full run there (20,000 x 60, 20 inactive), coolant void, 1,200 vs 2,100 K, isotope variants |
| `thermal.py` | Pin-bundle, cermet-block, salt-loop and heat-pipe sizing; Li boiling margin; He natural circulation; precursor drift; He Brayton cycle |
| `db_facts.py`, `calphad_mo_re.py` | Read-only database queries and the one CALPHAD calculation |
| `summarize.py` | Comparison table plus inventory (t HM/MWth, kg Pu/MWth) and W/Mo transmutation rate |

## Conventions and limits

- Infinite homogeneous medium: no leakage, no blankets, no self-shielding between fuel and coolant.
  k_inf = 1.15 is the common allowance for leakage of a large core; small cores (B6) need much more.
- Conversion ratio = (fertile captures in U-234, U-238, Pu-238, Pu-240) / (absorptions in U-235, Pu-239, Pu-241),
  as in `infinite.py`. Pu-242 counts as a parasitic absorber.
- Coolant void: coolant removed, other volume fractions fixed.
- Temperature effect: the whole homogenised medium moves from 1,200 to 2,100 K (fuel Doppler plus coolant and
  structure broadening); no density change.
- Carbon is C-12 only and He is He-4 only (C-13 and He-3 not in the library). W isotopes "enriched" means 95%
  of one isotope (assumption; no target in the brief).
- After a worker restart on 2026-11-20 the B1 and B4 scan points, B1 void worth and B1/B4 temperature effects were
  recovered from the run log (marked `note` in the JSON); those k values carry 20,000 x 60 statistics.

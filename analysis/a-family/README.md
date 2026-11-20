# Family A (aluminium-cooled) Phase 1 screening

Scripts and results behind [docs/studies/a-family-screening.md](../../docs/studies/a-family-screening.md) and the
"Phase 1 screening (2026-11-20)" sections of [A1](../../docs/designs/A1.md), [A2](../../docs/designs/A2.md) and
[A3](../../docs/designs/A3.md).

## Rerun

```bash
export PATH=/opt/mamba/envs/nuc/bin:$PATH
cd /home/user/fsn
python analysis/a-family/geometry.py          # unit-cell volume fractions (prints)
python analysis/a-family/chemistry.py         # JANAF + COST 507 checks   -> results/chemistry.json   (~2 min)
python analysis/a-family/thermal.py           # 1D sizing and cycles       -> results/thermal.json     (seconds)
python analysis/a-family/neutronics.py --workers 2   # OpenMC screens     -> results/neutronics_cases.json, critical_pu.json
python analysis/a-family/summarize.py         # derived worths and tables  -> results/summary.json, summary.md
```

`neutronics.py` caches each case by name and specification, so a rerun only computes missing or changed
cases. It needs `data/openmc/cross_sections.xml`. Each case is an infinite homogenised medium
(`analysis/common/infinite.py`), 20,000 particles x 60 batches (20 inactive), one thread; ~45 cases take
roughly 1-2 h on two shared cores.

## Files

| File | Content |
| --- | --- |
| `materials.py` | Compositions and (approx.) densities; Pu vector and depleted U; N-15 99.9%, B-11 99.9% |
| `geometry.py` | Volume fractions: A2 reference cell (67% fuel, W 11.1%, AlN 2.4%, Al 19.6%); A1 pin cell (assumed) |
| `neutronics.py` | Stage 1 Pu scans; stage 2 perturbations at the Pu fraction for k_inf = 1.15 |
| `chemistry.py` | Nitride/oxide stability, AlN dissociation, diboride nitriding, Al2O vapour (JANAF); N, Ti, Zr, B solubility in liquid Al (COST 507, ZrB2 added from JANAF); mass-transfer ceiling |
| `thermal.py` | A1 hot-pin sizing, A3 window and delayed-neutron retention, cycle limits |
| `summarize.py` | Void, Doppler, isotope and coolant-swap worths from the cached cases |
| `results/` | JSON outputs, `summary.md` tables, `run.log` |

## Main assumptions

- Infinite medium: no leakage, no blankets, no heterogeneity. k_inf = 1.15 is the rough target for a large
  core. Uniform density changes of a single homogeneous medium (A3) do not change k_inf, so A3 has no
  meaningful void worth in this model.
- Densities (g/cm3, approx.): liquid U-Pu 16.0, (U,Pu)N 13.6, Al 2.10 (2,100 K) or 2.20 (1,600 K), W 19.0,
  AlN 3.20, ZrB2 6.00, Na 0.80 and Pb 9.50 (hypothetical at these temperatures, comparison only).
  A3 solution density from ideal mixing of molar volumes.
- Temperatures: A1 1,600 K (interpolated between the 1,200 and 2,100 K libraries), A2 and A3 2,100 K.
- The conversion ratio is the proxy from `infinite.py`: fertile captures / fissile absorptions in the core
  only (no blanket).

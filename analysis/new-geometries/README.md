# New core geometries: Phase 1 scoping

Scripts behind [docs/studies/new-geometries-scoping.md](../../docs/studies/new-geometries-scoping.md):
first-cut neutronics, thermal limits and chemistry for the geometry candidates S5, S6, S8, S9, L3, L5 and
L7 from [docs/studies/geometry-by-phase.md](../../docs/studies/geometry-by-phase.md), compared with the A2
reference homogenisation.

| Script | Does | Output |
| --- | --- | --- |
| `materials.py` | Shared material definitions: Pu vector, depleted U, N-15, densities (approx.), natural abundances from the database restricted to library nuclides | (module) |
| `db_facts.py` | Read-only database queries: fast absorption (MT 101, U-235 fission spectrum), SGTE melting points, Al and Pb vapour pressures, Al2O3 heat capacity, AlN decomposition pressures (vacuum and under Al) | `results/db_facts.json` |
| `thermal.py` | Governing heat-transfer limit and implied size per candidate: radiative flux and area (L7, S9), fluidisation window (S5), gas pumping (S6), granular-flow h (S8), pin and film conduction (L3, L5); L7 plate and tube cells, gap gas, AlN evaporation into vacuum, hydrostatic stress | `results/thermal.json` |
| `neutronics.py` | `analysis/common/infinite.py` screen: Pu/(U+Pu) at k_inf = 1.15 (secant search), conversion ratio, median flux energy, coolant-void worth | `results/neutronics.json`, logs `results/neutronics_stream*.log` |
| `finite.py` | Finite homogenised cylinder (H = D) with a 40 cm depleted-U blanket: clean-critical Pu fraction and breeding-ratio proxy for L7 at its thermal size vs A2 at 3.3 m3 | `results/finite.json` |
| `summarise.py` | Merges the above into one table per candidate | `results/summary.csv`, `results/summary.json` |
| `run_all.sh` | Waits for `data/openmc/cross_sections.xml`, then runs `neutronics.py` with the given cases | |

Run order: `db_facts.py`, `thermal.py`, `neutronics.py`, `finite.py`, `summarise.py`
(`export PATH=/opt/mamba/envs/nuc/bin:$PATH` first). Neutronics uses threads=1; bracketing runs
10,000 x 40 batches (15 inactive), final and void runs 20,000 x 60 (20 inactive).

## Common assumptions

- Pu vector (approx., reactor-grade): Pu-238 2, Pu-239 60, Pu-240 24, Pu-241 9, Pu-242 5 atom %. U: 0.25 % U-235.
- N-15 at 99.9 % in UN, ZrN and AlN. Pb natural (no isotope tailoring).
- Liquid U-Pu 16.0 g/cm3; (U,Pu)N 13.6; W 19.0; Mo 10.0; AlN 3.26; liquid Al 2.15; liquid Pb 9.3; He 7 MPa 0.0024;
  ZrN 7.09; Al2O3 3.95 (all approx.). Vacuum gaps are He at 1e-9 g/cm3.
- Liquid-fuel cases at 2,100 K (library maximum; the fuel runs at ~2,270-2,400 K, so Doppler is slightly
  understated), solid-fuel He and particle cases at 1,500 K.
- Library substitutions: O-16 only for O, C-12 only for C (O-17/18, C-13 missing; < 1.1 at%). Everything
  else in the compositions is in the library.

## Limits

Infinite homogeneous medium: no leakage, no self-shielding between fuel and coolant regions, no blanket
(conversion ratio is a core-only proxy). `finite.py` adds leakage and a blanket for two cases only. All
thermal properties are approximate; emissivities at 2,000 °C, granular-flow heat transfer and the AlN
evaporation coefficient are the least certain inputs.

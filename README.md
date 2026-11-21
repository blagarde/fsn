# FSN: high-temperature fast breeder reactor study

Physics-first exploration of fast-spectrum breeder reactors that deliver heat at 850 °C and above, for electricity or direct industrial use. Regulation and cost are out of scope for now.

**Start here: [docs/README.md](docs/README.md)**: map of the problem space, designs, materials, studies and decisions.

| Area | Where |
| --- | --- |
| Project brief, targets, roadmap | [docs/project/](docs/project/) |
| Design taxonomy and materials screening method | [docs/framework/](docs/framework/) |
| Candidate designs (one page each) | [docs/designs/](docs/designs/README.md) |
| Materials (one page each, facts from the database) | [docs/materials/](docs/materials/README.md) |
| Studies (cross-cutting analyses) | [docs/studies/](docs/studies/README.md) |
| Decisions | [docs/decisions/](docs/decisions/README.md) |
| Open questions and go/no-go tests | [docs/open-questions.md](docs/open-questions.md) |
| Property database (code, sources, usage) | [docs/data/database.md](docs/data/database.md), package `htfbr_data/` |

## Most promising design options

**Updated:** 2026-11-21, after the [geometry and reflector refinement](docs/studies/geometry-by-phase.md#refinement-with-the-core-thermal-model-2026-11-21), the [R1 cross-check](docs/designs/R1.md#cross-check-with-the-core-thermal-model-2026-11-21), the [core nuclear-thermal study](docs/studies/core-thermal.md), the [new-geometries scoping](docs/studies/new-geometries-scoping.md) and the A-family Phase 1 chemistry in the [aluminium-coolant study](docs/studies/aluminium-coolant.md). All screening-level: homogenised models, no burnup, chemistry only where noted. Update this section after every study (see [conventions](docs/README.md#conventions)).

| Rank | Option | Why it is promising | What could kill it | Key numbers (1,000 MWth) | Next step |
| --- | --- | --- | --- | --- | --- |
| 1 | [R1](docs/designs/R1.md) radiatively coupled liquid U–Pu, Al in AlN panels (family R, with [R2](docs/designs/R2.md) Pb and [R3](docs/designs/R3.md) He variants) | No material touches both fuel and coolant; fuel at ~2,000 °C, Al out at 1,500–1,650 °C; breeds; a panel breach is negative reactivity; rides out total loss of cooling for ~1 h | Emissivity of W at 2,000 °C (bare W makes it 2.4× bigger); Pu inventory and doubling time unless tubes are made small (5 mm bore) and power is zoned; almost no prompt feedback in liquid U–Pu ([Q-052](docs/open-questions.md)); positive Al void worth | ~1,500 m² of tube surface with radial power zoning (twice that without). Inventory set by tube bore: 123 t fuel / 7.8 t fissile at 10 mm bore radius, 58 t / 3.9 t at 5 mm, 35 t / 2.7 t at 3 mm. BR ≈ 1.7 with blanket | Emissivity test ([Q-040](docs/open-questions.md)); smaller tubes; movable heavy reflector for control |
| 2 | [A2](docs/designs/A2.md) liquid U–Pu pool, Al in W/AlN tubes | Compact and fast-breeding: smallest Pu inventory of the hot options, Al outlet ~1,750 °C | One wall wetted by liquid U and liquid Al ([Q-030](docs/open-questions.md)); at the fuel limit the wall carries 13 MW/m², 4× its ceiling; +5,000 pcm Al void worth; fuel limit 30 s after losing cooling | 1–3 m³, 0.7–3 t fissile, BR ≈ 1.9 with blanket | Capsule tests of W and ZrB2 in liquid U and Al; redesign for ≤ 3 MW/m² |
| 3 | (U,Pu)N pins in lead (B-family type: [B2](docs/designs/B2.md), [B5](docs/designs/B5.md)) | Best transient behaviour found: Doppler and negative Pb void worth; settles at 8% power after loss of flow without scram; solid fuel keeps its prompt feedback | Lower outlet (~1,200 °C) than the liquid-fuel options; cladding and structures in lead above ~550 °C (chemistry not yet screened at T4) | ~5 m³, 2.2 t fissile, 203 MW/m³, Pb 24 t/s | B-family Phase 1 neutronics (in progress) |
| 4 | [X1](docs/designs/X1.md)–[X3](docs/designs/X3.md) liquid U–Pu at ~2,000 °C with Pb behind W, or direct contact with CaF2 or boiling Ca | Highest delivery temperature (1,800–1,900 °C); X2/X3 have no hot heat-transfer wall | Same weak liquid-fuel feedback; U–W mass transfer; carry-over and emulsions in direct contact | Not yet sized | X-family Phase 1 (in progress) |
| Seed | S6 printed lattice, He (draft "P1") | Particle-like heat path with an ordered geometry | He pumping (~26 MW); printability and irradiation of struts | 10 m³, 57 t fuel | Open as a seed family ([scoping](docs/studies/new-geometries-scoping.md)) |

**Parked or ruled out:** the 650 °C sodium branch ([D-0001](docs/decisions/D-0001-no-sodium-branch.md)); gas-fuel cores (cannot breed); He-cooled particle cores (15% of power spent on pumping); circulating liquid fuel (keeps only 55% of delayed neutrons); fluidised bed, particle-cooled core and falling film ([scoping](docs/studies/new-geometries-scoping.md)); natural boron anywhere in the core; ZrN against aluminium.

**Cross-cutting findings that steer every option:**
- Fissile density sets core size, not power. Power is whatever the heat path can remove at the temperature limit.
- Molten U–Pu has almost no Doppler feedback in its hard spectrum, so its prompt feedback is purely geometric: only leakage through walls that do not move as the liquid rises counts. OpenMC, 1,500→3,000 K: a tall free-surface pool −6,700 pcm, a wide shallow one −1,200, a laterally confined slab ~−150. Reflectors halve the critical mass but also the feedback (W, Pb, depleted U ≈ −3,500; BeO −2,200); end reflectors keep it (−5,350). A movable heavy reflector (worth 21,000–26,000 pcm) is the natural control for liquid fuel.
- With turbine inlet capped at 1,500 °C, a helium Brayton cycle gives ~54% at any outlet above ~1,550 °C. Hotter outlets pay off only for direct industrial heat or better turbine materials.
- Liquid aluminium dissolves every Al-facing wall material faster above ~1,500 °C; loop life is a dissolution-kinetics test, not a calculation.

## Getting started

```bash
bash setup/install_env.sh && export PATH=/opt/mamba/envs/nuc/bin:$PATH
htfbr-data build          # build the property database from primary sources
htfbr-data docs           # regenerate doc indexes and database facts in material pages
python -m pytest          # code tests, plus doc link and index checks
```

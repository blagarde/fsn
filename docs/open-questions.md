# Open questions and go/no-go tests

Numbered so design and material pages can point at them. Close a question by recording the answer and its evidence here (and a decision if it changes direction); do not delete rows.

**Kinds:** `decision` (needs a choice by us), `calc` (computable with our tools), `data` (needs a reference value entered), `test` (needs an experiment).

## Project scope

| ID | Question | Kind | Blocks | Status |
| --- | --- | --- | --- | --- |
| Q-001 | Which one or two heat-use cases anchor the reference design, and how far from the industrial plant may the reactor sit? | decision | [industrial heat](studies/industrial-heat.md) | open |
| Q-002 | Is reprocessing in scope? Doubling time depends on out-of-core inventory and cycle time as much as on BR. | decision | all breeders | open |
| Q-003 | Is a cold-vessel layout (hot core inside a vessel kept ≤ 550 °C) acceptable? It widens structural options. | decision | B1–B6 | open |
| Q-004 | Confirm targets, taxonomy axes and starting screening weights (gate G0). | decision | [roadmap](project/roadmap.md) | open |
| Q-006 | L7 radiatively coupled pool already chosen as design family R ([D-0007](decisions/D-0007-prioritise-radiative-coupling.md)). Which other geometries from the [geometry study](studies/geometry-by-phase.md) become design families (candidates: S6 printed lattice, S5 fluidised bed, L3 liquid-fuel pins, L5 falling film, L7 radiatively coupled pool, S8 particle-cooled core), and should geometry (axis 11) and heat-transport mode (axis 12) join the taxonomy? | decision | new designs | open |
| Q-005 | Approve the [materials selection method](framework/materials-selection.md) details (steps S1–S6, element pre-screen thresholds, chemistry rules R1–R10, ±40 kJ margin). Search strategy P1–P7 already adopted ([D-0006](decisions/D-0006-materials-search-strategy.md)) | decision | all material choices | open |

## Screening

| ID | Question | Kind | Blocks | Status |
| --- | --- | --- | --- | --- |
| Q-010 | Infinite-medium k∞, BR and phase windows for seed branches B1–B6 | calc | [B1–B6](designs/README.md) | open |
| Q-011 | Cross sections averaged over real fast-core spectra (OpenMC) rather than the U-235 fission spectrum | calc | all neutronics rankings | open |
| Q-012 | Reference thermochemistry for species missing from JANAF: Y2O3, ThO2, UO2, HfO2, UN; Sn vapour (Sn melting point now from SGTE) | data | [Al boundaries](studies/aluminium-coolant.md), fuels | open |
| Q-014 | Actinide CALPHAD assessments: U–Pu–Zr, U–Fe, U–Cr, U–W, U–Ta, U–Al, Ca–U, Pb–U, U–N, Al–Pb (see [coverage](data/calphad-coverage.md)); needs TDBDB, NIMS CPDDB, NIST, MSTDB-TC or paper supplements | data | X1–X3, A2, fuels | open |
| Q-013 | Settle JANAF vs handbook boiling points (Al, Na, Ca, Si, LiF, NaCl differ by 1–2.4%) with a second source | data | [claims check](data/claims-check.md) | open |

## Liquid fuel at ~2,000 °C

| ID | Question | Kind | Blocks | Status |
| --- | --- | --- | --- | --- |
| Q-020 | Mutual solubility of U–Pu with Pb, Ca, CaF2 and W at 1,500–2,100 °C (CALPHAD, then crucible tests) | calc → test | [X1](designs/X1.md), [X2](designs/X2.md), [X3](designs/X3.md), [A2](designs/A2.md) | open |
| Q-021 | Thermal-gradient mass transfer of W in liquid U–Pu | test | [X1](designs/X1.md), [A2](designs/A2.md) | open |
| Q-022 | Fuel carry-over and emulsion stability in direct-contact columns | calc → test | [X2](designs/X2.md), [X3](designs/X3.md) | open |
| Q-023 | Reactivity worth of carrier volume fraction and Ca vapour voids, including calcium's fast absorption (~147 mb fission-spectrum average, mostly MeV-range Ca-40(n,p) and (n,α); needs the real core spectrum, Q-011) | calc | [X2](designs/X2.md), [X3](designs/X3.md) | open |
| Q-024 | Fission-product partitioning between fuel, carrier and cover gas; off-gas decay heat; Pu vapour transport | calc | X1–X3, A2 | open |
| Q-025 | Freeze, drain and restart of a U–Pu pool; volume change on freezing | calc | X1–X3, A2, [D-0003](decisions/D-0003-no-cr-fe-in-liquid-fuel.md) | open |

## Aluminium coolant and A2

| ID | Question | Kind | Blocks | Status |
| --- | --- | --- | --- | --- |
| Q-030 | **Go/no-go:** do ZrB2 (B-11) and W/AlN survive liquid U at 2,000 °C and liquid Al at 1,800 °C for ~1,000 h? | test | [A2](designs/A2.md), [A1](designs/A1.md), [A3](designs/A3.md) | open |
| Q-031 | Is Pb immiscible with Al at 1,800–1,900 °C (needed for the Pb-bonded wall)? | calc → test | [A2](designs/A2.md) | open |
| Q-032 | Does nitrogen-saturated Al re-seal cracks in AlN? | test | [A2](designs/A2.md) | open |
| Q-033 | Monte Carlo BR, critical Pu fraction and coolant-density/void worth for Al-cooled cores vs Na and Pb | calc | A1–A3 | open |
| Q-034 | 3D CFD of one A2 bundle cell: does natural convection change fuel-side heat transfer? (1D estimate: Nu ≈ 1) | calc | [A2](designs/A2.md) | open |
| Q-035 | U–Al breach energetics: heat release, mixing and pressure | calc → test | [A2](designs/A2.md) | open |
| Q-036 | Hot-leg solubility of Zr, Ti and Al2O in Al (sets loop life) | calc | A1–A3 | open |

## Radiatively coupled family (R1–R3)

| ID | Question | Kind | Blocks | Status |
| --- | --- | --- | --- | --- |
| Q-040 | Emissivity of textured and ZrC-coated W at 1,800–2,200 °C, held ≥ 1,000 h (bare W at ε ≈ 0.3 makes the core 2.4× larger) | test | [R1](designs/R1.md), [R2](designs/R2.md), [R3](designs/R3.md) | open |
| Q-041 | Evaporation coefficient of AlN in vacuum and under ~1 bar N2 at 1,300–1,600 °C (JANAF upper bound 0.8–29 m/yr in vacuum) | test | [R1](designs/R1.md) | open |
| Q-042 | Does liquid fuel in a radiatively cooled tube stay near-isothermal (coolant entering at the top)? | calc | R1–R3 | open |
| Q-043 | Allowed fuel-column height in W tubes (hydrostatic hoop stress ~1.6 MPa per metre, creep at 2,000 °C) and feeding of a tiered core | calc | R1–R3 | open |
| Q-044 | Heterogeneous / 3D Monte Carlo of R1–R3 (current numbers are homogenised) | calc | R1–R3 | open |
| Q-045 | Freeze and restart control when fuel and coolant are coupled only by radiation | calc | R1–R3, Q-025 | open |
| Q-046 | Emissive coatings for Mo receivers facing vacuum (bare Mo gives 0.27 MW/m² instead of 0.76) | test | [R2](designs/R2.md), [R3](designs/R3.md) | open |
| Q-047 | Spectrum class of liquid U–Pu cores: median flux energy ~196 keV puts A2 and R1 in class F, not H | decision | [taxonomy](framework/taxonomy.md), A2, R1–R3 | open |
| Q-048 | Parked geometries: S5 fluidisation window, S8 wall heat-transfer coefficient, S6 printability and strut irradiation | calc → test | [scoping study](studies/new-geometries-scoping.md) | open |

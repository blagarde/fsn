# Roadmap

Current phase: **Phase 1, data and broad screening** (property database started 2026-11-20).

## Phases and gates

| Phase | Work | Exit gate |
| --- | --- | --- |
| 0 Framework | Brief, taxonomy, screening method | G0: targets, taxonomy and weights agreed |
| 1 Data and broad screening | Property database; screen ~100–200 taxonomy combinations with simple models (k∞, BR, phase windows, cycle efficiency) | G1: ≤ 10 concepts |
| 2 Concept scoping | 3D Monte Carlo with depletion, 1D thermal-hydraulics, compatibility analysis | G2: 2–3 concepts |
| 3 Pre-conceptual design | Coupled multiphysics, transients, uncertainty quantification | G3: one reference concept |
| 4 Conceptual design and validation plan | Experiments and irradiations needed; regulation brought back in | — |

## Next steps

- [ ] Confirm or revise the [target figures of merit](brief.md#target-figures-of-merit), especially outlet temperature and BR
- [ ] Agree the [taxonomy axes and exclusion rules](../framework/taxonomy.md)
- [ ] Challenge the [starting weights](../framework/materials-screening.md#stage-2-figures-of-merit)
- [x] Pick the reference nuclear data library: ENDF/B-VIII.0 (JEFF-3.3 and JENDL-5 hosts not yet allowed, see [sources](../data/database.md#sources))
- [x] Pick the Monte Carlo code: OpenMC 0.16 installed with NJOY2016
- [ ] Database v1: replace every *(approx.)* figure with a sourced value and uncertainty ([progress](../data/claims-check.md))
- [ ] Hand-enter the reference values JANAF lacks (Y2O3, ThO2, UO2, HfO2, Sn) from SGTE, Konings 2014, NEA-TDB
- [ ] Run k∞ / BR / phase-window screening for branches [B1–B6](../designs/README.md)
- [ ] Average cross sections over real fast-core spectra (OpenMC) instead of the U-235 fission spectrum
- [ ] Choose anchor heat-use cases ([Q-001](../open-questions.md))
- [ ] Obtain actinide CALPHAD assessments ([Q-014](../open-questions.md)): request TDBDB, NIMS CPDDB and NIST hosts, or enter paper supplements
- [ ] Approve the [materials selection method](../framework/materials-selection.md) ([Q-005](../open-questions.md)), then build its tooling: element pre-screen report, compatibility register, R1 exchange-reaction calculator

## Change log

| Date | Change |
| --- | --- |
| 2026-11-18 | Phase 0 framework written (brief, state of the art, taxonomy, screening) |
| 2026-11-19 | Sodium branch dropped ([D-0001](../decisions/D-0001-no-sodium-branch.md)); industrial heat, ~2,000 °C liquid fuel and aluminium coolant studies; A2 feasibility |
| 2026-11-20 | Property database (IAEA LiveChart, ENDF/B-VIII.0, NIST-JANAF) and claims check; docs moved to this repository ([D-0005](../decisions/D-0005-docs-in-repo.md)) |

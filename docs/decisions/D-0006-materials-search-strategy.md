# D-0006: Materials search strategy (guiding principle)

- **Date:** 2026-11-20
- **Status:** accepted
- **Affects:** [materials selection method](../framework/materials-selection.md#guiding-principle-search-without-enumerating-reject-only-on-evidence), [materials screening](../framework/materials-screening.md), all material and design choices

## Context

Each design combines many components, each drawn from many candidate materials (pure elements, alloys, compounds, salts), with isotopic, temperature and pressure choices on top. The full cross product (~10¹² combinations before continuous variables) cannot be enumerated. A naive filter risks discarding good combinations on weak evidence.

## Decision

Materials selection follows seven principles (P1–P7):
- pairwise checking;
- interval treatment of temperature and pressure;
- best-case screening of design choices such as enrichment;
- element-level pruning only for additive properties;
- constraint propagation instead of enumeration;
- asymmetric error control;
- a cheap-to-expensive fidelity ladder keeping several survivors per branch.

Asymmetric error control means:
- rejection needs evidence E1–E3;
- every rejection is logged and re-screened when data change;
- each run is repeated with relaxed thresholds to produce a near-miss list;
- the rules are calibrated against known working systems.

## Consequences

- Screening tools must record why each candidate was rejected and support relaxed re-runs.
- A rule that would reject a calibration case (`config/calibration_cases.yaml`) is a bug and must be fixed before use.
- Estimates (Miedema, DFT, judgement) can keep options alive but never eliminate them on their own.
- The rest of the selection method (thresholds, rules R1–R10) is still awaiting approval under [Q-005](../open-questions.md); this principle stands regardless of how those details change.

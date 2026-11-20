# D-0001: No sodium-cooled branch

- **Date:** 2026-11-19
- **Status:** accepted
- **Affects:** [taxonomy exclusion rule 1](../framework/taxonomy.md#exclusion-rules)

## Context

Sodium boils at ~883 °C (JANAF: 897 °C at 1 bar). With a ~300 K boiling margin it cannot reach the ≥ 850 °C outlet target at low pressure. A ~650 °C sodium branch was proposed as a lower-risk fallback.

## Decision

No sodium (or NaK, K) branch is kept, not even as a fallback.

## Consequences

Sodium-cooled reactors stay in the state of the art as references only. Revisit only if the outlet-temperature target drops below ~650 °C.

# D-0004: W/AlN is the reference A2 tube wall

- **Date:** 2026-11-19
- **Status:** accepted
- **Affects:** [A2](../designs/A2.md), [tungsten](../materials/tungsten.md), [aluminium nitride](../materials/aluminium-nitride.md), [zirconium diboride](../materials/zirconium-diboride.md)

## Context

Sizing showed monolithic ZrB2 is thermal-stress limited to ~1–1.5 MW/m² at 1.5 mm, while tungsten reaches ~3 MW/m² with stresses it relaxes by creep; W and AlN expansion coefficients match.

## Decision

W (fuel side) with an AlN layer (aluminium side) is the reference wall; monolithic ZrB2 (thinner) and the Pb-bonded double wall stay as alternatives.

## Consequences

AlN crack tolerance becomes the key risk. Revisit after the capsule tests ([Q-030](../open-questions.md)).

---
id: calcium-fluoride
title: Calcium fluoride
formula: CaF2
kind: compound
roles: [carrier]
status: candidate
updated: 2026-11-20
---

# Calcium fluoride

The strongest direct-contact carrier candidate ([X2](../designs/X2.md)): a salt, not a metal, that does not mix with molten uranium and separates by density, as slag does in metallothermic uranium production. Low vapour pressure at 2,000 °C.

## Database facts

<!-- BEGIN GENERATED db-facts -->
| Property | Value | Source |
| --- | --- | --- |
| Melting point | 1,418 °C | NIST-JANAF (crystal <--> liquid row) |
| Boiling point (1 bar) | 2,531 °C | NIST-JANAF |
| Vapour pressure at 1,500 °C | 0.000244 bar | NIST-JANAF |
| Vapour pressure at 2,000 °C | 0.0403 bar | NIST-JANAF |
| ΔfG° at 298 K | -1,173 kJ/mol | NIST-JANAF |
| ΔfG° at 1,500 K | -976 kJ/mol | NIST-JANAF |
| ΔfG° at 2,000 K | -883 kJ/mol | NIST-JANAF |
<!-- END GENERATED -->

## Compatibility

| Partner | Verdict | Basis |
| --- | --- | --- |
| Liquid U–Pu metal | Compatible (immiscible) | CaF2 more stable than U fluorides; slag–metal separation in U production |
| Tungsten | Compatible | W fluorides much less stable |

## Neutronics and activation

Clean activation: F-20 (11 s). Fluorine moderates mildly. Calcium's fast absorption is high (~147 mb fission-spectrum average, see [calcium](calcium.md)), so the carrier volume fraction in the core must be kept small ([Q-023](../open-questions.md)).

## Open issues

- Fuel carry-over and emulsion stability in a direct-contact column.
- Fission-product partitioning between fuel and salt.

## Used by designs

<!-- BEGIN GENERATED used-by -->
- [X2](../designs/X2.md): Liquid U-Pu pool, CaF2 direct contact
<!-- END GENERATED -->

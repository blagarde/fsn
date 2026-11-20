---
id: calcium
title: Calcium
formula: Ca
kind: element
roles: [carrier]
status: candidate
updated: 2026-11-20
---

# Calcium

Proposed as a boiling direct-contact carrier in [X3](../designs/X3.md): essentially immiscible with uranium, light (density ~1.2 g/cm³ at 2,000 °C *(approx.)*), and it boils inside the fuel to carry heat out as vapour.

## Database facts

<!-- BEGIN GENERATED db-facts -->
| Property | Value | Source |
| --- | --- | --- |
| Natural isotopes | Ca-40 (96.9%), Ca-42 (0.647%), Ca-43 (0.135%), Ca-44 (2.09%), Ca-46 (0.004%), Ca-48 (0.187%) | IAEA LiveChart |
| Capture, at 0.0253 eV | 0.438 b | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Capture, U-235 fission-spectrum average | 1.55 mb | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Absorption (non-fission), at 0.0253 eV | 0.441 b | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Absorption (non-fission), U-235 fission-spectrum average | 147 mb | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Moderating parameter ξ | 0.0491 | computed from mean atomic mass 40.078 u (LiveChart) |
| Melting point | 842 °C | NIST-JANAF (crystal <--> liquid row) |
| Boiling point (1 bar) | 1,501 °C | NIST-JANAF |
| Vapour pressure at 1,500 °C | 0.995 bar | NIST-JANAF |
| Vapour pressure at 2,000 °C | 9.22 bar | NIST-JANAF, Clausius–Clapeyron extrapolation above Tb |
<!-- END GENERATED -->

## Compatibility

| Partner | Verdict | Basis |
| --- | --- | --- |
| Uranium | Compatible (immiscible) | Ca reduces UF4 to U metal in industrial production |
| Tungsten | Compatible | No intermetallics |

## Neutronics and activation

Near-clean activation: Ca-41 (long-lived, weak) and Ca-45 from Ca-44. **But calcium absorbs fast neutrons strongly in a fission spectrum** (database facts above): Ca-40(n,p) (~110 mb) and Ca-40(n,α) (~40 mb) switch on at MeV energies, held back below that by the Coulomb barrier, so the real penalty depends on how hard the core spectrum is. The earlier claim that calcium is a low-absorption carrier was wrong; the penalty depends on carrier volume fraction and core spectrum ([Q-023](../open-questions.md)).

## Open issues

- U and Pu solubility in liquid Ca at 2,000 °C.
- Void reactivity from vapour in the fuel.

## Used by designs

<!-- BEGIN GENERATED used-by -->
- [X3](../designs/X3.md): Liquid U-Pu pool, boiling calcium direct contact
<!-- END GENERATED -->

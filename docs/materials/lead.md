---
id: lead
title: Lead
formula: Pb
kind: element
roles: [coolant, bond]
status: candidate
updated: 2026-11-20
---

# Lead

High boiling point and almost no moderation make lead the classic fast-reactor heavy coolant. Above ~550 °C it attacks steels and nickel alloys, so T3+ designs need refractory or ceramic boundaries. Also proposed as the monitored liquid bond in [A2's double wall](../designs/A2.md#mitigating-the-tube-wall-risk).

## Database facts

<!-- BEGIN GENERATED db-facts -->
| Property | Value | Source |
| --- | --- | --- |
| Natural isotopes | Pb-204 (1.4%), Pb-206 (24.1%), Pb-207 (22.1%), Pb-208 (52.4%) | IAEA LiveChart |
| Capture, at 0.0253 eV | 0.174 b | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Capture, U-235 fission-spectrum average | 1.85 mb | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Absorption (non-fission), at 0.0253 eV | 0.174 b | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Absorption (non-fission), U-235 fission-spectrum average | 1.85 mb | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Moderating parameter ξ | 0.00962 | computed from mean atomic mass 207.217 u (LiveChart) |
| Melting point | 327 °C | NIST-JANAF (crystal <--> liquid row) |
| Boiling point (1 bar) | 1,746 °C | NIST-JANAF |
| Vapour pressure at 1,500 °C | 0.23 bar | NIST-JANAF |
| Vapour pressure at 2,000 °C | 3.26 bar | NIST-JANAF, Clausius–Clapeyron extrapolation above Tb |
<!-- END GENERATED -->

## Compatibility

| Partner | Verdict | Basis |
| --- | --- | --- |
| Steels | Conditional, ≤ ~550 °C | Dissolved-oxygen control needed |
| Ni alloys | Incompatible | High Ni solubility |
| W, Mo, SiC | Compatible | Very low solubility |
| Uranium | Uncertain | UPb and UPb3 intermetallics; likely dissolves U at 2,000 °C |
| Aluminium | Assumed immiscible (to confirm) | Liquid miscibility gap reported; needed for A2's lead bond |

## Neutronics and activation

Clean activation: Pb-209 (3.25 h) → Bi-209; trace Po-210 via Bi-209 capture. Enriched Pb-206/207 would cut Bi and Po further.

## Open issues

- U–Pb and Al–Pb mutual solubility at 1,800–2,000 °C.

## Used by designs

<!-- BEGIN GENERATED used-by -->
- [A2](../designs/A2.md): Liquid U-Pu pool cooled by aluminium
- [B2](../designs/B2.md): Lead-cooled nitride
- [B5](../designs/B5.md): Lead-cooled cermet
- [R2](../designs/R2.md): Radiatively coupled liquid U-Pu, lead-cooled Mo panels
- [X1](../designs/X1.md): Liquid U-Pu pool, lead behind tungsten tubes
<!-- END GENERATED -->

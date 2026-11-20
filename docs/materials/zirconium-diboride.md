---
id: zirconium-diboride
title: Zirconium diboride (B-11)
formula: ZrB2
kind: compound
roles: [wall, cladding, heat exchanger]
status: candidate
updated: 2026-11-20
---

# Zirconium diboride (B-11)

Top candidate for a single wall facing both liquid uranium and liquid aluminium: melts at ~3,245 °C *(approx.)*, conducts heat well, and diborides resist molten aluminium in smelting cells. The boron must be ≥ 99.5–99.9% B-11, because B-10 is a strong absorber (thermal (n,α) 3,844 b, database). B-11 is the by-product of B-10 enrichment.

## Database facts

<!-- BEGIN GENERATED db-facts -->
| Property | Value | Source |
| --- | --- | --- |
| ΔfG° at 298 K | -318 kJ/mol | NIST-JANAF |
| ΔfG° at 1,500 K | -296 kJ/mol | NIST-JANAF |
| ΔfG° at 2,000 K | -283 kJ/mol | NIST-JANAF |
<!-- END GENERATED -->

## Compatibility

| Partner | Verdict | Basis |
| --- | --- | --- |
| Liquid Al | Compatible (to confirm) | Diboride cathodes in Hall–Héroult cells; Zr leaching to Al3Zr to check |
| Liquid U | Probably compatible | UB2 much less stable than ZrB2; Zr–U exchange to check |
| W | Conditional | Possible W boride formation at high temperature; graded interlayer |

## Neutronics and activation

Zr captures little; residual B-10 drives helium production and swelling. Brittle: thermal stress limits heat flux to ~1–1.5 MW/m² at 1.5 mm wall ([A2](../designs/A2.md#heat-flux-trade-off)).

## Open issues

- Zr solubility in Al at temperature; boron exchange with U; irradiated toughness.

## Used by designs

<!-- BEGIN GENERATED used-by -->
- [A1](../designs/A1.md): Solid nitride fuel, aluminium-cooled
- [A2](../designs/A2.md): Liquid U-Pu pool cooled by aluminium
- [A3](../designs/A3.md): Al-U-Pu solution fuel
<!-- END GENERATED -->

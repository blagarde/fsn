---
id: aluminium-nitride
title: Aluminium nitride
formula: AlN
kind: compound
roles: [wall coating, heat exchanger]
status: candidate
updated: 2026-11-20
---

# Aluminium nitride

Aluminium's own nitride, so stable against liquid aluminium; conducts heat well and matches tungsten's thermal expansion. The reference aluminium-facing layer of [A2's](../designs/A2.md) W/AlN wall. In core it needs N-15, because N-14 captures neutrons and makes C-14.

## Database facts

<!-- BEGIN GENERATED db-facts -->
| Property | Value | Source |
| --- | --- | --- |
| ΔfG° at 298 K | -287 kJ/mol | NIST-JANAF |
| ΔfG° at 1,500 K | -153 kJ/mol | NIST-JANAF |
| ΔfG° at 2,000 K | -95 kJ/mol | NIST-JANAF |
<!-- END GENERATED -->

## Compatibility

| Partner | Verdict | Basis |
| --- | --- | --- |
| Liquid Al | Compatible | Own nitride; keep Al nitrogen-saturated to stop slow dissolution |
| Liquid U | Marginal | UN about as stable as AlN; nitrogen can move into the fuel |
| W | Compatible | No stable W nitride; expansion match |

## Neutronics and activation

N-14(n,p)C-14 is the main parasitic reaction; N-15 enrichment removes it.

## Open issues

- Decomposition pressure and dissolution rate in Al at 1,800–2,000 °C.
- Whether nitrogen-saturated Al re-seals cracks.

## Used by designs

<!-- BEGIN GENERATED used-by -->
- [A1](../designs/A1.md): Solid nitride fuel, aluminium-cooled
- [A2](../designs/A2.md): Liquid U-Pu pool cooled by aluminium
- [A3](../designs/A3.md): Al-U-Pu solution fuel
- [R1](../designs/R1.md): Radiatively coupled liquid U-Pu, aluminium-cooled AlN panels
<!-- END GENERATED -->

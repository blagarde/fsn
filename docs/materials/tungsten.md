---
id: tungsten
title: Tungsten
formula: W
kind: element
roles: [wall, vessel, cermet matrix]
status: candidate
updated: 2026-11-20
---

# Tungsten

The natural wall and vessel material for liquid U–Pu fuel: melts at ~3,400 °C, forms no compounds with uranium, and is barely attacked by Pb, Ca or CaF2. It must never touch liquid aluminium (WAl12 forms).

## Database facts

<!-- BEGIN GENERATED db-facts -->
| Property | Value | Source |
| --- | --- | --- |
| Natural isotopes | W-180 (0.12%), W-182 (26.5%), W-183 (14.3%), W-184 (30.6%), W-186 (28.4%) | IAEA LiveChart |
| Capture, at 0.0253 eV | 18.1 b | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Capture, U-235 fission-spectrum average | 54.9 mb | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Absorption (non-fission), at 0.0253 eV | 18.1 b | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Absorption (non-fission), U-235 fission-spectrum average | 54.9 mb | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Moderating parameter ξ | 0.0108 | computed from mean atomic mass 183.842 u (LiveChart) |
| Melting point | 3,407 °C | NIST-JANAF (crystal <--> liquid row) |
<!-- END GENERATED -->

## Compatibility

| Partner | Verdict | Basis |
| --- | --- | --- |
| Liquid U–Pu | Compatible (mass transfer to measure) | No intermetallics; solubility unknown at 2,000 °C |
| Pb, Ca, CaF2 | Compatible | Very low solubility / no reaction |
| Liquid Al | Incompatible | WAl12 and other aluminides |
| AlN | Compatible | No stable W nitride; expansion coefficients match |
| Air / oxygen | Incompatible above ~500 °C | Catastrophic oxidation; inert guard volume needed |

## Neutronics and activation

Significant fast-neutron capture (see database facts); transmutation to Re and Os forms brittle phases, slower in a fast spectrum. Isotope-tailored W (more W-184/186) reduces both. Creep strength only a few MPa at 2,000 °C; irradiation raises the brittle transition.

## Open issues

- U–W solubility and thermal-gradient mass transfer at 2,000 °C.
- Irradiated ductility and creep at 1,600–2,000 °C.

## Used by designs

<!-- BEGIN GENERATED used-by -->
- [A1](../designs/A1.md): Solid nitride fuel, aluminium-cooled
- [A2](../designs/A2.md): Liquid U-Pu pool cooled by aluminium
- [B1](../designs/B1.md): Lithium-cooled nitride
- [B2](../designs/B2.md): Lead-cooled nitride
- [B5](../designs/B5.md): Lead-cooled cermet
- [X1](../designs/X1.md): Liquid U-Pu pool, lead behind tungsten tubes
- [X2](../designs/X2.md): Liquid U-Pu pool, CaF2 direct contact
- [X3](../designs/X3.md): Liquid U-Pu pool, boiling calcium direct contact
<!-- END GENERATED -->

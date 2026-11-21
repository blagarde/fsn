---
id: aluminium
title: Aluminium
formula: Al
kind: element
roles: [coolant, carrier]
status: candidate
updated: 2026-11-20
---

# Aluminium

Thermally the best liquid-metal coolant in the study: liquid from 660 °C to ~2,500 °C at near-atmospheric pressure, high volumetric heat capacity and conductivity, ~5× less pumping power than sodium and ~20× less than lead *(approx., from handbook ρ, μ, k)*. Its weakness is chemistry: molten aluminium dissolves almost every structural metal and reduces most ceramics. Full analysis: [aluminium coolant](../studies/aluminium-coolant.md).

## Database facts

<!-- BEGIN GENERATED db-facts -->
| Property | Value | Source |
| --- | --- | --- |
| Natural isotopes | Al-27 (100%) | IAEA LiveChart |
| Capture, at 0.0253 eV | 0.233 b | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Capture, U-235 fission-spectrum average | 0.541 mb | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Absorption (non-fission), at 0.0253 eV | 0.233 b | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Absorption (non-fission), U-235 fission-spectrum average | 5.25 mb | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Moderating parameter ξ | 0.0723 | computed from mean atomic mass 26.982 u (LiveChart) |
| Melting point | 660 °C | NIST-JANAF (crystal <--> liquid row) |
| Boiling point (1 bar) | 2,518 °C | NIST-JANAF |
| Vapour pressure at 1,500 °C | 0.000593 bar | NIST-JANAF |
| Vapour pressure at 2,000 °C | 0.0544 bar | NIST-JANAF |
<!-- END GENERATED -->

## Compatibility

| Partner | Verdict | Basis |
| --- | --- | --- |
| Steels, Ni alloys | Incompatible | Aluminide formation (FeAl3, NiAl3); rapid erosion in foundry practice |
| W, Mo, Ta, Nb, Zr | Incompatible | Aluminides (WAl12, MoAl12, TaAl3, NbAl3, ZrAl3) |
| Uranium, plutonium | Incompatible (reacts) | UAl2–UAl4 form; U + 2Al → UAl2 is exothermic |
| Graphite, SiC | Incompatible | Al4C3 forms |
| SiO2, TiO2, ZrO2, UO2, Si3N4 | Incompatible | Reduced (aluminothermic); see [oxide stability](../studies/aluminium-coolant.md#why-the-usual-boundaries-fail) |
| Al2O3, AlN | Compatible | Aluminium's own compounds; Al2O3 eroded by Al2O vapour above ~1,500 °C |
| Y2O3, CaO, ThO2 | Compatible | More stable than Al2O3 (NIST-JANAF where available) |
| ZrB2, TiB2 | Compatible (to confirm at temperature) | Diboride cathodes in aluminium smelting at ~960 °C |
| Water | Hazard | Molten Al–water steam explosions; no steam generator in the loop |

## Neutronics and activation

Single stable isotope (Al-27). Activation is short-lived: Al-28 (2.2 min) in operation, Na-24 (15 h) via fast (n,α), Mg-27 from (n,p) decays back to Al. No tritium or polonium. Moderates per atom about as much as sodium, but liquid Al has about twice the atom density.

## Open issues

- Coolant-void worth and breeding-ratio penalty against Na and Pb (Monte Carlo).
- Solubility of Zr, Ti and Al2O in Al at the hot-leg temperature sets loop life.
- Liquid density, viscosity and conductivity at 1,500–2,000 °C to enter from Assael et al. (2006) and other references.

## Used by designs

<!-- BEGIN GENERATED used-by -->
- [A1](../designs/A1.md): Solid nitride fuel, aluminium-cooled
- [A2](../designs/A2.md): Liquid U-Pu pool cooled by aluminium
- [A3](../designs/A3.md): Al-U-Pu solution fuel
- [R1](../designs/R1.md): Radiatively coupled liquid U-Pu, aluminium-cooled AlN panels
<!-- END GENERATED -->

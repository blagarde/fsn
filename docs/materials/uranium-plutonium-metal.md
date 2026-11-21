---
id: uranium-plutonium-metal
title: Liquid uranium–plutonium metal
formula: U
kind: fuel
roles: [fuel]
status: candidate
updated: 2026-11-20
---

# Liquid uranium–plutonium metal

The only fuel family that is liquid at ~2,000 °C at near-zero pressure: uranium melts at ~1,130 °C and boils around 4,100 °C. Densest fuel and hardest spectrum, so the highest breeding potential. Chromium or iron additions would lower the freezing point but cost a little breeding; default is none ([D-0003](../decisions/D-0003-no-cr-fe-in-liquid-fuel.md)). Database facts below are for uranium.

## Database facts

<!-- BEGIN GENERATED db-facts -->
| Property | Value | Source |
| --- | --- | --- |
| Natural isotopes | U-234 (0.0054%), U-235 (0.72%), U-238 (99.3%) | IAEA LiveChart |
| Capture, at 0.0253 eV | 3.38 b | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Capture, U-235 fission-spectrum average | 69.5 mb | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Absorption (non-fission), at 0.0253 eV | 3.38 b | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Absorption (non-fission), U-235 fission-spectrum average | 69.5 mb | ENDF/B-VIII.0 via NJOY2016, natural abundances |
| Moderating parameter ξ | 0.00838 | computed from mean atomic mass 238.029 u (LiveChart) |
<!-- END GENERATED -->

## Compatibility

| Partner | Verdict | Basis |
| --- | --- | --- |
| W, Ta | Compatible (mass transfer to measure) | No intermetallics |
| Y2O3, ThO2 | Compatible | Not reduced |
| CaF2, Ca | Compatible (immiscible) | Metallothermic U production |
| Al, Sn, Cu, Si | Incompatible | Form uranium intermetallics |
| Pb | Uncertain | UPb, UPb3 |
| Fe, Cr, Ni | Low-melting eutectics | U–Fe ~725 °C, U–Cr ~860 °C |

## Neutronics and activation

Pu-239 delayed-neutron fraction ~0.0021: keep the pool stationary so precursors stay in the core. At 2,000 °C volatile fission products (Xe, Kr, Cs, I, much of Sm and Eu) leave the fuel, removing poisons online.

## Open issues

- Thermophysical properties of liquid U–Pu at 1,500–2,100 °C (k, μ, ρ, β): IAEA-THPH (2008) and literature to enter.
- Pu vapour transport (~mbar) into the cover gas.

## Used by designs

<!-- BEGIN GENERATED used-by -->
- [A2](../designs/A2.md): Liquid U-Pu pool cooled by aluminium
- [R1](../designs/R1.md): Radiatively coupled liquid U-Pu, aluminium-cooled AlN panels
- [R2](../designs/R2.md): Radiatively coupled liquid U-Pu, lead-cooled Mo panels
- [R3](../designs/R3.md): Radiatively coupled liquid U-Pu, helium-cooled Mo tubes, direct Brayton
- [X1](../designs/X1.md): Liquid U-Pu pool, lead behind tungsten tubes
- [X2](../designs/X2.md): Liquid U-Pu pool, CaF2 direct contact
- [X3](../designs/X3.md): Liquid U-Pu pool, boiling calcium direct contact
<!-- END GENERATED -->

# Study: aluminium as coolant

Thermally, aluminium is the best liquid-metal coolant in this study: liquid from 660 °C to ~2,500 °C at near-atmospheric pressure, ~5× less pumping power than sodium and ~20× less than lead, barely absorbing neutrons, with activation that decays within minutes to days. The price is chemistry: molten aluminium dissolves every structural metal and reduces most ceramics. Boundaries must come from a short list: aluminium's own compounds ([Al2O3](../materials/alumina.md), [AlN](../materials/aluminium-nitride.md)), oxides more stable than Al2O3 ([Y2O3](../materials/yttria.md), [ThO2](../materials/thoria.md), CaO), and diborides made with boron-11 ([ZrB2](../materials/zirconium-diboride.md), TiB2).

Material facts: [aluminium](../materials/aluminium.md). Designs: [A1](../designs/A1.md), [A2](../designs/A2.md) (analysed), [A3](../designs/A3.md). The oxide-stability chart is in the Claude Doc (tab *Aluminium coolant*).

## Properties against other liquid-metal coolants

Rows tagged *(db)* were verified against the [property database](../data/claims-check.md); others are *(approx.)* until handbook values are entered.

| Property (Al, Pb, Sn at 1,000 °C; Na at 600 °C) | Al | Na | Pb | Sn |
| --- | --- | --- | --- | --- |
| Melting / boiling point (°C) *(db, JANAF)* | 660 / 2,518 (handbooks 2,470) | 98 / 897 (handbooks 883) | 327 / 1,746 | 232 / 2,602 *(not in JANAF)* |
| Vapour pressure at 1,500 °C *(db)* | 0.0006 bar | far above boiling | 0.23 bar | — |
| Vapour pressure at 2,000 °C *(db)* | 0.054 bar | — | 3.3 bar (extrapolated) | — |
| Density (g/cm³) | ~2.3 | ~0.81 | ~9.9 | ~6.5 |
| Specific heat (kJ/kg·K) | 1.18 *(db)* | ~1.27 | ~0.14 | ~0.24 |
| Volumetric heat capacity (MJ/m³·K) | ~2.7 | ~1.0 | ~1.4 | ~1.6 |
| Thermal conductivity (W/m·K) | ~100 | ~60 | ~20 | ~30 |
| Relative pumping power, equal heat and ΔT | 1 | ~5 | ~20 | ~11 |
| Thermal capture cross section (b) *(db, ENDF/B-VIII.0)* | 0.234 | 0.528 | 0.174 | 0.607 |
| Moderating parameter ξ *(db)* | 0.072 | 0.085 | 0.0096 | 0.017 |
| Main activation *(db half-lives)* | Al-28 (2.2 min); Na-24 (15 h) via fast (n,α) | Na-24 (15 h) | Pb-209 (3.25 h) | Sn-113, Sn-123 |
| Reaction with water / air | Steam explosions with water; protective oxide in air | Violent | Mild | Mild |

Pumping power scales as μ^0.2 / (ρ² cp^2.8) in turbulent flow. Aluminium is an excellent electrical conductor, so sealless electromagnetic pumps (standard in the aluminium industry) work well.

## Neutronics and activation

- Al-27 is the only stable isotope; capture is comparable to sodium and far below steel.
- Moderation per atom is close to sodium, but liquid Al has ~2× the atom density: expect a somewhat softer spectrum than a sodium core. BR penalty and coolant-void worth need Monte Carlo ([Q-033](../open-questions.md)).
- Activation is short-lived: Al-28 (2.2 min), Na-24 (15 h) via fast (n,α) (fission-spectrum average 0.72 mb, db); Mg-27 from (n,p) decays back to Al; Al-26 needs > 13 MeV neutrons.
- Transmutation slowly adds Si and Mg at ppm per year.

## Why the usual boundaries fail

1. **Aluminide formation**: stable intermetallics with almost every transition metal (FeAl3, NiAl3, WAl12, MoAl12, NbAl3, TaAl3, ZrAl3, UAl2–UAl4).
2. **Carbide formation**: graphite and SiC turn into Al4C3.
3. **Reduction**: any oxide or nitride less stable than aluminium's own is reduced (thermite chemistry).

Oxide stability at 25 °C, kJ per mol O2 (magnitude of ΔfG°), *(db, NIST-JANAF)* unless noted: Al2O3 1,055 (threshold); more stable: CaO 1,207, BeO 1,158 (excluded, moderator), MgO 1,138 (excluded, Mg boils off at high temperature); less stable (reduced by Al): ZrO2 1,040, TiO2 883, SiO2 854. Not in JANAF, values *(approx.)*: Y2O3 ~1,211, ThO2 ~1,169, HfO2 ~1,088 (excluded, absorber), UO2 ~1,032. High-temperature comparison from JANAF is a next step.

## Boundary candidates

| Material | Melts / decomposes (°C) | Against liquid Al | Against liquid U–Pu | Conductivity at high T (W/m·K) | Expansion (10⁻⁶/K) | Best role |
| --- | --- | --- | --- | --- | --- | --- |
| [ZrB2](../materials/zirconium-diboride.md) with B-11 | ~3,245 | Stable (smelting cells); check Zr leaching | Probably stable | ~60 | ~6–7 | **Single wall for both fluids** |
| TiB2 with B-11 | ~3,230 | Stable (drained cathodes) | Probably stable | ~50–70 | ~7–8 | Alternative |
| [AlN](../materials/aluminium-nitride.md) (N-15 in core) | ~2,200–2,500 (N2-pressure dependent) | Stable (own nitride) | Marginal | ~60–100 | ~4.5–5.5 | **Al-side layer of W/AlN wall** |
| [Al2O3](../materials/alumina.md) | 2,054 *(db; handbooks ~2,072)* | Stable < ~1,500 °C | Marginal | ~6 | ~8–9 | Cold leg, insulation |
| [Y2O3](../materials/yttria.md) | ~2,425 | Stable | Stable | ~3–5 | ~8 | Liner |
| [ThO2](../materials/thoria.md) | ~3,390 | Stable | Stable | ~3 | ~9.5 | Breeding liner |
| CaO | ~2,613 | Stable | Stable | Low | ~13 | Lab crucibles |
| W, Ta, Mo, Nb, steels, Ni alloys | — | Dissolve | W, Ta good | — | — | Fuel side only |
| Graphite, SiC, Si3N4, SiO2, ZrO2, MgO, BeO | — | Carbided or reduced | — | — | — | Excluded |

Through a 2 mm wall with 200 K across it, ZrB2 or AlN pass ~6 MW/m², tungsten ~10 MW/m², Y2O3 or ThO2 only ~0.3 MW/m².

## Aluminium-cooled architectures

| Design | Fuel | Boundary | Coolant outlet | Main risk |
| --- | --- | --- | --- | --- |
| [A1](../designs/A1.md) | (U,Pu)N pins | ZrB2 (B-11) or W/AlN cladding | 1,200–1,600 °C | Brittle cladding under fission-gas pressure |
| [A2](../designs/A2.md) | Liquid U–Pu pool | ZrB2 or W/AlN tubes | ~1,700–1,880 °C | Tube wall survival (critical) |
| [A3](../designs/A3.md) | U, Pu dissolved in Al | None between fuel and coolant | 1,600–2,000 °C | Low heavy-metal density; precursor drift |

## Loop-wide implications

- Every wetted surface (pumps, piping, valves, exchangers) comes from the short list; hot leg ZrB2 or AlN, cold leg Al2O3 or Y2O3 linings.
- No water anywhere near; helium or N2 Brayton, or a salt intermediate loop.
- Al grabs oxygen (Al2O3 inclusions, ceramic foam filters) and dissolves hydrogen (degassing).
- Al shrinks ~6–7% on freezing *(approx.)*: frozen pipes do not burst; sequence re-melting.
- Oxide skin prevents wetting below ~1,000 °C; good wetting at operating temperature.
- Hot-leg solubility of Zr, Ti or Al2O sets loop life.

## First calculations

[Q-030](../open-questions.md) to [Q-035](../open-questions.md): CALPHAD for Al–Zr–B, Al–Ti–B, Al–N, U–Zr–B, U–Al–N; Monte Carlo BR and void worth; B-11 purity; W/AlN and W/ZrB2 interfaces; breach energetics; Al2O transport.

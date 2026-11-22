# Study: boiling-fuel "pressure cooker" reactor cooled by aluminium

**Status:** first analysis (2026-11-22). Concept from the project lead: a sealed vessel in which the fuel sits at its boiling point, cooled from outside by liquid aluminium (flowing or as a bath), relying on a negative void coefficient. Target ~1 GWth. Code: [`analysis/boiling-pool/`](../../analysis/boiling-pool/) (`model.py`, `study.py`, `neutronics.py`). Numbers are *(calc)* unless marked; vapour data are *(db)* (NIST-JANAF); liquid salt properties, creep strengths and actinide vapour data are *(approx.)* and listed in [Q-060–Q-063](../open-questions.md).

## Short answer

- **The void coefficient is strongly negative, as hoped.** Bubbles displace fuel. OpenMC gives −175 to −570 pcm per percent of void, so 10% void is worth 4–10 times β. Boiling shuts the core down hard.
- **Boiling cannot be the main way heat leaves the core.** At the 1–3 bar these fuels boil at near 2,000 K, a cubic metre of vapour carries only 0.7–2.7 MJ. A boiling pool held below 30% void can then carry only 0.1–3 MW/m³: **300–12,000 m³ of fuel per GW**, against 1–5 m³ for a normal fast core. The one exception is a magnesium carrier, which boils at ~32 bar at 2,000 K and carries 23 MJ/m³ (4–29 MW/m³). Its pressure at that temperature is beyond any hot vessel.
- **A single vessel cannot reach 1 GW.** Its outside wall carries only 20–110 MW at the wall's heat-flux limit (radius 1–2.5 m).
- **The concept works as a thermostat.** Run just below boiling, with heat removed by natural convection to Al-cooled walls (a tube bundle or an array of small vessels). Boiling then **caps the temperature** at the saturation point, and the cover-gas pressure sets where that cap is. The fuel that fits is **liquid U–Pu metal under a boiling carrier (Pb or Ca)**: 250–500 m² of cooled wall per GW at 2–4 MW/m². Chloride and fluoride salts conduct heat too poorly for this.
- **The vessel is the hardest material problem, as expected.** Hot-wall (wall at fuel temperature): only W or W-25Re hold the pressure at ~2,000 K, at 1–2 bar and small radius, with a TiB2 or AlN outer layer against the Al. Cold-wall (the user's suggestion of continuous outside cooling): a frozen-fuel skull protects any refractory wall and lets the fuel inside be far hotter, but heat must flow downhill through the skull: the Al stays below the fuel's solidus (~1,380 K) minus the wall's temperature drop. That puts it at ~1,150–1,300 K (≈850–1,030 °C), lower at higher heat flux, whatever the fuel temperature.

## What boils, and what its vapour can carry

No actinide compound or U–Pu metal has vapour data in the database. U–Pu metal boils at ~3,500 K (Pu-driven) to ~4,400 K (U) *(approx.)*. So the boiling liquid is either the **solvent of a fuel salt** (NaCl, LiF), with the actinide salt taken as non-volatile (Raoult's law, *(approx.)*), or a **carrier metal in contact with molten U–Pu** (Pb, Ca, Mg), as in [X1](../designs/X1.md) and [X3](../designs/X3.md).

| Boiling system at 2,000 K | Pressure | Vapour density | Latent heat | Heat per m³ of vapour | Flooding limit, 1 m tube |
| --- | --- | --- | --- | --- | --- |
| NaCl–(U,Pu)Cl3, 30% NaCl | 0.99 bar | 0.36 kg/m³ | 2.58 MJ/kg | 0.94 MJ/m³ | 34 MW/m² |
| NaCl–(U,Pu)Cl3, 50% NaCl | 1.7 bar | 0.64 | 2.50 | 1.60 | 38 |
| ⁷LiF–(U,Pu)F4, 60% LiF | 0.55 bar | 0.11 | 6.42 | 0.68 | 70 |
| U–Pu under boiling Pb | 0.91 bar | 1.14 | 0.86 | 0.97 | 43 |
| U–Pu under boiling Ca | 3.1 bar | 0.75 | 3.64 | 2.72 | 70 |
| U–Pu under boiling Mg | 31.9 bar | 4.67 | 4.91 | **22.9** | 208 |
| U–Pu metal itself at 3,500 K (Pu vapour) | 0.15 bar | 0.12 | 1.39 | 0.17 | — |

Vapour pressures, densities and latent heats come from JANAF dimer and trimer data *(db)*. Above an element's boiling point they are extrapolated by Clausius–Clapeyron. The flooding limit is the counter-current limit of a closed thermosyphon (Faghri et al. 1989 *(approx.)*), per m² of cross-section. **For comparison**, a boiling-water reactor at 70 bar has ~55 MJ/m³, which is why it can boil at reactor power densities.

## Mode A: boiling carries the heat

All heat leaves as vapour that condenses on the Al-cooled walls; the liquid is stagnant. Void comes from drift flux (Zuber–Findlay, churn-turbulent). The power density at which the pool's mean void reaches 30% is:

| Boiling system (2,000 K) | Pool 0.3 m deep | 1 m | 2 m | Fuel volume per GW at 1 m |
| --- | --- | --- | --- | --- |
| NaCl–(U,Pu)Cl3, 30% NaCl | 0.53 MW/m³ | 0.16 | 0.08 | 6,200 m³ |
| NaCl–(U,Pu)Cl3, 50% NaCl | 0.94 | 0.28 | 0.14 | 3,500 m³ |
| ⁷LiF–(U,Pu)F4 | 0.40 | 0.12 | 0.06 | 8,300 m³ |
| U–Pu under boiling Pb | 0.70 | 0.21 | 0.11 | 4,700 m³ |
| U–Pu under boiling Ca | 3.2 | 0.97 | 0.49 | 1,000 m³ |
| U–Pu under boiling Mg (32 bar) | 29 | 8.7 | 4.3 | 115 m³ |
| U–Pu metal itself (3,500 K) | 0.15 | 0.05 | — | ~20,000 m³ |

Pumping the liquid upward through the core (as a BWR does) sweeps bubbles out faster. That raises these figures by roughly 10–20× at a few m/s *(approx.)*, still well short of a fast core's 200–900 MW/m³. **The limit is the vapour volume itself: 1 GW makes ~1,000 m³/s of salt vapour at 1 bar.** This finding does not depend on the vessel material.

### Architectures for 1 GW in mode A (chloride, 2,000 K, W-25Re + TiB2 wall, Al at 1,500 K)

| Architecture | Power limited by | Result |
| --- | --- | --- |
| Single vessel, R 1.0 / 1.5 / 2.5 m, Al on the outside | Wall: 21 / 44 / 113 MW. Flooding: 105 / 237 / 659 MW. **Void ≤ 30%: 0.5 / 1.1 / 3.1 MW** | One vessel cannot reach 1 GW in either mode |
| Small sealed boiling vessels ("pins"), r 2.5–5 cm, in flowing Al | Void: 0.3–1.3 kW per pin | 0.8–3.2 million pins, 1,900–6,200 m³ of fuel |
| One boiler with external Al-cooled condensers (vapour piped out of the core) | Void at the pool | 1,900–6,200 m³ of fuel, a pool ~90 m across |

## Mode B: boiling as a thermostat

Heat leaves by natural convection inside the liquid to Al-cooled walls. In operation the fuel stays **below** boiling, and the cover-gas pressure sets the saturation temperature. On overpower or loss of cooling the hottest fuel reaches saturation, bubbles form, and the core shuts down within a few percent of void (see the void worths below). The temperature cannot run away, and the cap can be moved by changing the cover-gas pressure. The heat-removal question is then the same as for the stationary-pool designs.

Internally heated liquid between cooled surfaces, Nu = 0.34 Ra^0.226 *(approx.)*:

| Fuel | Half-gap between cooled walls | Power density | Fuel-to-wall drop | Wall flux | Wall area per GW |
| --- | --- | --- | --- | --- | --- |
| Liquid U–Pu metal | 1 cm | 300 MW/m³ | 145 K | 3.0 MW/m² | 330 m² |
| Liquid U–Pu metal | 3 cm | 50 / 300 MW/m³ | 94 / 377 K | 1.5 / 9.0 MW/m² | 670 / 110 m² |
| NaCl–(U,Pu)Cl3 | 1 cm | 50 MW/m³ | 363 K | 0.5 MW/m² | 2,000 m² |
| NaCl–(U,Pu)Cl3 | 3 cm | 50 MW/m³ | 944 K | 1.5 MW/m² | 670 m² |

**Liquid metal fits; salt does not.** Salt conducts about 100× worse, so its temperature drop to the wall is several hundred kelvin even at low power density. With the wall flux capped at 2–4 MW/m² (vessel section below), a U–Pu core needs **250–500 m² of cooled wall per GW**. That means a tube bundle in the pool ([A2](../designs/A2.md) G1/G2, [X1](../designs/X1.md)) or an array of small Al-cooled vessels (L3 pins). The boiling carrier can be Pb (saturation 2,020 K at 1 bar, ~2,300 K at ~3 bar) or Ca (1,770 K at 1 bar, 2,000 K at 3 bar). It can be a thin layer on top of the fuel or dispersed in it. **This is the 1 GW form of the pressure cooker**: an A2- or X1-type core whose temperature is capped by a boiling carrier at a pressure the operator sets.

## The vessel

### Hot wall (wall near fuel temperature)

Duplex wall: refractory metal on the fuel side, carrying the pressure, plus a 1 mm ceramic layer on the Al side. Every refractory metal forms aluminides with liquid Al, so the barrier is needed. A-family Phase 1 found its dissolution limit in Al: ZrB2 ~1,770 K, AlN ~1,840 K, TiB2 ~1,950 K ([aluminium study](aluminium-coolant.md)). Checks: hoop stress P·r/t ≤ ⅔ of the 10⁴ h creep-rupture strength *(approx.)*; metal thermal stress ≤ 3× that (it relaxes); ceramic thermal stress ≤ half its fracture strength; Al-side face below the barrier's dissolution limit. The metal thickness is optimised for each case.

Largest heat flux through the wall: fuel at 2,000 K (chloride vapour pressure ×1.5 margin), TiB2 barrier, Al at 1,500 K:

| Material | r = 2.5 cm (pins, tubes) | r = 25 cm | r = 1.5 m (single vessel) | Compatibility (fuel side / Al side) |
| --- | --- | --- | --- | --- |
| W | 4.3 MW/m² (barrier stress) | 2.5 (metal thermal stress) | 1.9 (Al-side temperature) | Noble against chlorides and U–Pu-free salts; W–U mass transfer open ([Q-021](../open-questions.md)) / needs a barrier |
| W-25Re | 4.3 | 4.3 | 0.85 (metal thermal stress, 7 mm wall) | As W; ductile at room temperature / needs a barrier |
| Mo (TZM) | 4.3 | **fails** (creep) | 0.34 | Noble against chlorides / needs a barrier |
| Ta-10W | 4.2 | **fails** | 0.11 | TaCl5 more stable: attacked by oxidising salt / needs a barrier |
| Re | 4.3 | 2.2 | 0.35 | Noble; strong neutron absorber, costly / needs a barrier |
| Nb-1Zr | **fails** | **fails** | **fails** | Too weak above ~1,500 K |

**Reading:** small radii are easy, because stress scales with P·r/t and a thin wall carries little thermal stress. There the **ceramic barrier's thermal stress (~4 MW/m²)** is the limit, so the barrier, not the metal, sets the wall flux. Large vessels are hard: at r = 1.5 m only W and W-25Re carry useful flux, and Mo, Ta and Nb fail on creep. So **a hot "pressure cooker" must be many small vessels or tubes, not one large one**, and only at 1–3 bar. A magnesium carrier at 32 bar is impossible in a hot wall.

### Cold wall with a frozen-fuel skull (continuous outside cooling)

Keep the vessel's inner face below the fuel's melting point (U-rich U–Pu ~1,350–1,400 K *(approx.)*). A crust of frozen fuel then forms on it. The wall only ever touches solid fuel at its own temperature, and the liquid inside can be far hotter: 2,000 K, or even boiling U–Pu at ~3,500 K. This is the cold-crucible principle used to melt Ti, Zr and UO2.

| Wall inner face | Al bulk | Max wall flux (Mo-TZM, TiB2, r 1.5 m, 2 bar) | Skull thickness at 3 MW/m² |
| --- | --- | --- | --- |
| 1,100 K | 950 K | 2.8 MW/m² (Al-side temperature) | 2.8 mm |
| 1,100 K | 1,050 K | 0.9 MW/m² | — |
| 1,250 K | 950 K | 4.3 MW/m² (barrier stress) | 1.3 mm |
| 1,250 K | 1,050 K | 3.7 MW/m² | — |

What the skull buys:
- Any refractory metal holds pressure easily at ~1,200 K: Mo-TZM is ~10× stronger than at 2,000 K.
- No liquid fuel ever touches the wall, which removes the hardest chemistry question (W, Mo or Ta in liquid U).
- A pressure-cooker vessel at 30 bar becomes feasible, so the Mg carrier can be reconsidered.

What it costs:
- **The aluminium must run below the skull temperature.** The skull's inner face sits at the fuel solidus (~1,380 K). The wall face must be below it by enough to keep a crust of useful thickness. The Al is below that again by the temperature drop through the wall, barrier and film, which is proportional to heat flux. Mo-TZM, 2 mm, plus TiB2 1 mm, h_Al = 50 kW/m²K:

  | Wall heat flux | Wall inner face | Skull | Highest Al bulk temperature |
  | --- | --- | --- | --- |
  | 0.5 MW/m² | 1,300 K | 4.8 mm | 1,270 K (≈1,000 °C) |
  | 1 MW/m² | 1,300 K | 2.4 mm | 1,240 K (≈970 °C) |
  | 2 MW/m² | 1,300 K | 1.2 mm | 1,180 K (≈910 °C) |
  | 3 MW/m² | 1,300 K | 0.8 mm | 1,120 K (≈850 °C) |

  The floor is Al's melting point (933 K). The ceiling is the solidus. **The heat is delivered at ≈850–1,000 °C, set by the fuel's melting point and the heat flux, not by the fuel temperature.** Running hotter needs more wall area (1,000–2,000 m² per GW at 0.5–1 MW/m²) and a thinner skull, which is less forgiving of power swings. The 950–1,050 K settings in the table above are a conservative case. A 3,500 K boiling U–Pu core with a skull gains nothing in delivered temperature unless the hot fuel or its vapour is used directly, for example by radiation or a metal-vapour cycle.
- The 1,000–2,000 K drop between the liquid and the skull is an entropy loss.
- Skull thickness swings with power, which changes the fuel inventory and the heat path.

## Void reactivity (OpenMC)

Bubbles displace fuel at constant fuel mass, so the liquid column swells upward: density × (1 − α), height ÷ (1 − α). OpenMC on ENDF/B-VIII.0, σ ≈ 60–80 pcm:

| Pool | Size | Void 10% | 20% | 30% | Per % void |
| --- | --- | --- | --- | --- | --- |
| NaCl–(U,Pu)Cl3 30/70, Cl-37 99%, 3.0 g/cm³ at 2,000 K, Pb reflector 30 cm (Pu 10.5%) | R 1.5 m, H 3 m (21 m³) | −2,700 pcm | −6,500 | −11,200 | −270 to −370 |
| Liquid U–Pu, Pu 15%, W reflector 20 cm | R 16 cm, H 32 cm (critical) | −4,400 | −9,900 | −17,100 | −440 to −570 |
| Large core: 45% liquid U–Pu (Pu 10%) + 10% W, W reflector | R 1.5 m, H 3 m | −1,750 | −4,300 | −7,400 | −175 to −250 |

Chloride criticality at this size needs Pu ≈ 11–12% *(calc, by interpolation)*. **Every case is strongly negative**, even the large, reflected core, where expansion feedback was weak in the [core-thermal study](core-thermal.md). The reason: void displaces several percent of the fuel, against ~0.1% per 100 K for thermal expansion. Boiling is therefore a far stronger prompt feedback than anything else available to liquid metal fuel, and a direct answer to [Q-052](../open-questions.md), provided the fuel is allowed to reach saturation.

**Caveats:**
- **Boiling instabilities:** chugging, geysering and density-wave oscillations near saturation are a real risk in mode B. They need a coupled kinetics-boiling model ([Q-062](../open-questions.md)).
- **Fission gases** (Kr, Xe) collect in the vapour space as non-condensables and degrade condensation. Venting is needed.
- **Mass transfer:** a carrier boiling through Pu-bearing fuel carries Pu with it, and Pu is the more volatile actinide.

## Recommended form at ~1 GW

| Choice | Recommendation | Why |
| --- | --- | --- |
| Operating mode | B: thermostat (subcooled, boiling only above the set point) | Mode A needs 100–10,000× the normal core volume |
| Fuel | Liquid U–Pu metal (Pu 10–15%) | Conducts 100× better than salt; void worth −175 to −570 pcm per % |
| Boiling carrier | Pb (cap 2,020 K at 1 bar, ~2,300 K at ~3 bar) or Ca (1,770 K at 1 bar, 2,000 K at 3 bar) | Sets the cap by cover-gas pressure; Pb absorbs little; Ca is more volatile and boils more strongly |
| Heat removal | 250–500 m² of Al-cooled walls (tube bundle in the pool, or an array of small vessels), 2–4 MW/m² | Wall flux is limited by the Al-side ceramic barrier |
| Vessel, hot-wall | W or W-25Re tubes or small vessels (r ≤ 25 cm), 1–2 mm, with a 1 mm TiB2 (or AlN) outer layer; Al at ≤ 1,500 K | Only W-based alloys hold pressure near 2,000 K; TiB2 has the highest Al dissolution limit |
| Vessel, cold-wall alternative | Mo-TZM (or any refractory) with a frozen U–Pu skull; Al at ~1,150–1,270 K | Removes liquid-U chemistry and pressure limits, but delivers heat at ≈850–1,000 °C, capped by the fuel's melting point |

At the hot-wall settings, the core is close to [A2](../designs/A2.md) or [X1](../designs/X1.md) geometry. The new element is a **pressure-set boiling cap**, which supplies the strong prompt feedback that the core-thermal and geometry studies found missing for liquid U–Pu. The cold-wall variant is a different design point: robust chemistry, delivery temperature capped below the fuel's melting point.

## Open questions

- [Q-060](../open-questions.md): actinide vapour data, and vapour pressure of the actinide salts over NaCl and LiF solvents (not in JANAF). Also liquid salt density, viscosity and surface tension at 1,800–2,200 K (currently extrapolated).
- [Q-061](../open-questions.md): creep-rupture data for W, W-Re, Mo-TZM and Ta alloys at 1,600–2,200 K, entered with locators (currently order-of-magnitude).
- [Q-062](../open-questions.md): coupled boiling-kinetics model of mode B. Onset of boiling, void distribution, chugging and density-wave stability, and how sharp the temperature cap really is.
- [Q-063](../open-questions.md): skull behaviour: thickness, Pu segregation on freezing, stability under power changes. Also whether a hot-fuel use (radiation or metal-vapour cycle) can recover the temperature lost across the skull.

## How to run

```bash
cd analysis/boiling-pool
/opt/mamba/envs/nuc/bin/python study.py        # vapour, power density, walls, architectures, skull, thermostat
/opt/mamba/envs/nuc/bin/python neutronics.py   # OpenMC void worths (~20 min)
```

# Study: core geometry by phase of matter

**Status:** ideation (2026-11-20). Nothing here is a design yet; [Q-006](../open-questions.md) asks which geometries to develop into design pages.

Geometry decides how far heat must travel through the fuel, how many walls sit at peak temperature, how much coolant dilutes the core (and so the spectrum and breeding), and whether delayed neutrons stay in the core. This page lists the geometries open to each fuel phase, then crosses them with the phase of the coolant (nine heat-transport modes), with what each combination buys and costs for a high-temperature breeder. The taxonomy so far ([axes 1–10](../framework/taxonomy.md)) records fuel chemistry and coolant but not geometry; a proposed eleventh axis is at the end.

![Core geometries grouped by fuel phase: solid S1-S6, liquid L1-L6, gas or plasma G1-G5](../assets/figures/geometry-by-phase.svg)

## What geometry controls

| Quantity | Why it matters here | Geometry lever |
| --- | --- | --- |
| Heat path in the fuel | Peak fuel temperature, so how hot the coolant can be | Smaller pins, thinner plates, particles, liquid stirring |
| Walls at peak temperature | The hottest wall is usually the life-limiting part ([A2](../designs/A2.md#feasibility-scorecard)) | Fewer walls, walls away from the hottest point, or none (direct contact) |
| Coolant (or void) fraction in the core | Dilutes fuel and softens the spectrum, cutting breeding ratio; changes void reactivity | Tight lattices, dense beds, stationary pools |
| Delayed-neutron retention | Pu-239 has β ≈ 0.0021; precursors swept out of the core thin the control margin further | Keep fuel in the core (pools, pins); avoid fast external loops |
| Feedback | Prompt negative feedback limits transients | Liquid expansion, bed expansion, Doppler |
| Refuelling and processing | Burnup limit, poison removal, doubling time | Online for liquids and moving beds; batch for fixed solids |

### Heat path: the solid-fuel numbers

Temperature rise from fuel surface to centre is ΔT = q‴ a² / (n k), with a the half-thickness or radius and n = 2 (slab), 4 (cylinder), 6 (sphere). At q‴ = 500 MW/m³ in the fuel:

| Fuel element | ΔT, conductivity ~20 W/m·K (nitride-like) | ΔT, ~3 W/m·K (oxide-like) |
| --- | --- | --- |
| Pin, radius 4 mm | 100 K | 670 K |
| Pin, radius 2 mm | 25 K | 170 K |
| Plate, half-thickness 1 mm | 13 K | 83 K |
| Printed lattice strut, half-width 0.5 mm | 3 K | 21 K |
| Particle, radius 0.5 mm | 1 K | 7 K |

Conductivities are approximate. The point is the scaling: heat path falls with the square of size, so finely divided fuel all but removes the fuel's own temperature drop. The wall and coolant then set the limit.

## Solid fuel

Heat crosses the fuel, then a cladding or matrix wall, then the coolant. The coolant can be gas, liquid metal or salt.

| ID | Geometry | Heritage | For | Against | Fit for a T4–T5 breeder |
| --- | --- | --- | --- | --- | --- |
| S1 | Pin bundle (rods in wire wrap or grids) | Every SFR and LFR; EBR-II, BN-800 | Best-known; dense, low coolant fraction (~35–40% *(approx.)*) | Cladding is the hottest wall; fission-gas pressure loads it | Baseline for B1–B3, B5, [A1](../designs/A1.md); limited by cladding at T4+ |
| S2 | Plates (flat or curved, narrow channels) | Research reactors (MTR-type) | Short heat path; large surface | Plates bow and swell; flow blockage sensitivity | Good with dense ceramic fuel; under-explored for fast cores |
| S3 | Inverted block (fuel matrix pierced by coolant channels) | HTGR prismatic blocks (with graphite); proposed for fast cores | Fuel continuous, coolant in tubes; channel walls can be thin liners | Matrix cracking; thermal stress in a large block | Natural home for cermet fuel ([B5](../designs/B5.md)) |
| S4 | Packed particle bed (pebbles or coated particles between porous walls) | Pebble-bed HTGRs; particle-bed rocket reactors (moderated) | Tiny heat path, huge surface, high gas outlet temperature | ~40% void softens spectrum; local hot spots; moderating matrices must be replaced by dense ones for a fast core | Gas-cooled T4–T5 with dense coated particles (no graphite) |
| S5 | Fluidised bed (particles suspended by upward coolant flow) | Fluidised-bed concepts, rotating-bed rocket concepts *(approx.)* | Excellent heat transfer, online refuelling, bed expansion gives negative feedback | Reactivity noise from bubbling; particle erosion; void fraction varies with flow | Speculative but attractive for T5 gas or liquid-metal cooling |
| S6 | Printed lattice (fuel or fuel-bearing ceramic with designed channels, e.g. gyroid) | Printed SiC core structures (ORNL Transformational Challenge Reactor) | Heat path of particles with the order of a pin; channels optimised for flow | Manufacturing of dense fuel ceramics; inspection; irradiation behaviour of thin struts | New; worth a design page for He or Pb cooling |

## Liquid fuel

The fuel can move, so heat can be carried to a wall placed away from the hottest point, or to a carrier with no wall at all. Liquid metal fuel (U–Pu) and salt fuel (chloride, fluoride) both apply.

| ID | Geometry | Heritage | For | Against | Fit for a T4–T5 breeder |
| --- | --- | --- | --- | --- | --- |
| L1 | Circulating loop (fuel pumped through an external heat exchanger) | MSRE; MSFR and MCFR concepts; [B4](../designs/B4.md) | No in-core walls; online processing | Delayed-neutron precursors swept out; whole loop radioactive; external exchanger at peak temperature | Good for salts at T3; doubtful for Pu fuel at T5 (β loss) |
| L2 | Pool with immersed heat-exchanger tubes | [A2](../designs/A2.md) G1/G2, [X1](../designs/X1.md) | Fuel stays in core (precursors kept); low pressure | Thousands of walls at fuel temperature; fuel-side conduction drop (~200 K in A2) | Analysed (A2); wall survival is the go/no-go |
| L3 | Liquid-fuel pins (fuel sealed in vented tubes, coolant outside) | LAMPRE capsules; Moltex stable salt reactor; Dual Fluid concept | Breach stays local; heat path = pin radius | Many walls facing two fluids; venting fission gas | Promising for metal fuel with refractory or diboride pins |
| L4 | Direct contact (light immiscible carrier passed through the fuel) | Metallothermic U production (slag–metal); [X2](../designs/X2.md), [X3](../designs/X3.md) | No hot heat-transfer wall at all | Fuel carry-over; fission-product exchange; carrier absorption ([Ca](../materials/calcium.md)) | The boldest route past the wall problem |
| L5 | Falling film (thin fuel film flowing down a cooled wall, or free sheets) | Falling-film heat exchangers (chemical industry) | Very short heat path; large surface; drains by gravity | Film stability; wetting; criticality of thin films needs a large core or reflector | New; geometric advantage of plates with liquid fuel |
| L6 | Rotating annulus (molten fuel held against a spinning wall; coolant passes through) | Liquid-core rocket concepts *(approx.)* | Very high temperature; fuel held away from the wall by a cooler layer | Rotating seals and bearings at temperature; complex | Speculative; relevant only for T5 |

## Gas, vapour or plasma fuel

Heat leaves mainly as thermal radiation or as charged fission fragments, so the fuel never touches a wall it must conduct through.

| ID | Geometry | Heritage | For | Against | Fit for a T4–T5 breeder |
| --- | --- | --- | --- | --- | --- |
| G1 | Open gas core (fissioning gas or plasma held in a vortex of buffer gas) | NASA gas-core rocket studies | Fuel temperature 10,000 K+ possible | Fuel loss in the exhaust; huge critical cavities | Not a breeder |
| G2 | Closed gas core ("nuclear light bulb": plasma inside a transparent wall) | United Aircraft studies (1960s–70s) | Fuel contained; radiation passes through the wall | Wall transparency and cooling | Not a breeder |
| G3 | Vapour core (uranium tetrafluoride vapour) with MHD conversion | University of Florida vapour-core reactor concepts (1990s) | High efficiency claimed with MHD topping | Gas cores are low density, so they need moderated or heavily reflected cavities: thermal or epithermal spectrum | Not a breeder; possible topping stage |
| G4 | Fission-fragment direct conversion (thin fuel layers or fibres; fragments collected electrically) | Fission-fragment rocket and conversion concepts | Bypasses Carnot ([state of the art](../project/state-of-the-art.md#thermodynamic-ceilings)) | Fragments travel only microns in solids, so fuel must be thin; low power density | Long-range option only |
| G5 | Dust suspension (fine fuel particles carried in gas) | Dusty-plasma concepts | Online fuel handling; large surface | Erosion, deposition, criticality control | Speculative |

**Physics limit for this category:** a gas or plasma is roughly a thousand times less dense than a condensed fuel. A critical gas core therefore needs a very large cavity and usually a moderating reflector, which gives a thermal spectrum and rules out a fast breeder. Gas-phase concepts stay in the study as topping cycles or long-range options, not as breeder cores.

## Second dimension: phase of the coolant

The coolant's phase sets how heat leaves the core, what pressure the system runs at, and what touches the fuel's boundary. Nine heat-transport modes are open:

| Code | Coolant phase / mode | Examples | For | Against |
| --- | --- | --- | --- | --- |
| `K-S` | Solid conduction (no fluid in the core; heat conducts through solid to the core boundary) | Small space and micro-reactor monoliths | No pumps, no fluid chemistry | ΔT = q‴R²/4k grows with core size squared: a 0.3 m radius core at 10 MW/m³ and k = 50 W/m·K would need ~4,500 K. Micro-reactors only |
| `K-P` | Flowing granular solid (ceramic or metal particles as the heat carrier) | Falling-particle solar receivers (~1,000 °C) | No pressure, no boiling, inert ceramics up to very high temperature | Low heat-transfer coefficient (large surfaces needed); erosion; particle handling |
| `K-M` | Melting carrier (solid feed melts in the core, carrying latent plus sensible heat) | Your original idea in the [liquid-fuel study](liquid-fuel-2000c.md); latent-heat storage | Isothermal delivery at the melting point; high latent heat (silicon ~1.8 MJ/kg) | Feeding solid into a hot core; carrier activation and absorption |
| `K-L` | Single-phase liquid (liquid metal or salt) | SFR, LFR, molten-salt coolants; [A2](../designs/A2.md), [X1](../designs/X1.md) | High heat transfer at low pressure; well understood | Corrosion and mass transfer; freezing |
| `K-B` | Boiling / two-phase (boiling liquid metal, heat pipes, direct-contact boiling) | Heat-pipe micro-reactors; [X3](../designs/X3.md); [B6](../designs/B6.md) | Very high heat flux; isothermal; heat pipes are passive | Void reactivity; dry-out; boiling instabilities |
| `K-SC` | Supercritical fluid (above the critical point: no boiling, liquid-like density) | Supercritical CO2 cooling concepts; supercritical-water fast reactor concepts *(approx.)* | Direct Brayton cycle; dense, so good heat transfer | High pressure (~20–25 MPa); water moderates (low breeding), CO2 limited to ~700–850 °C by corrosion and dissociation |
| `K-G` | Single-phase gas | HTGRs, GFR concepts; [B3](../designs/B3.md) | Inert, transparent to neutrons, direct Brayton, very high temperature | High pressure; poor heat capacity; passive decay-heat removal hard |
| `K-PL` | Ionised gas / plasma (seeded gas heated to partial ionisation) | Closed-cycle MHD with alkali-seeded noble gas (~1,800–2,200 °C) *(approx.)*; seeded propellant in gas-core rockets | Direct MHD electricity from the coolant; extreme temperature | Electrode and channel erosion; seeding chemistry; immature |
| `K-R` | Radiative coupling (no coolant contact: fuel boundary radiates across a vacuum or inert gap to a cooled wall) | Space-reactor radiators; nuclear light bulb (G2) | **Splits the chemistry**: the fuel container touches only fuel; the coolant wall touches only coolant | Low flux at moderate temperature (below); needs large surfaces and high emissivity |

Radiative coupling flux, fuel boundary at T to a wall at 1,300 °C (net, two parallel grey surfaces):

| Hot side | Black surfaces | Emissivity 0.8 / 0.8 | Emissivity 0.3 / 0.8 (bare tungsten) |
| --- | --- | --- | --- |
| 1,500 °C | 0.21 MW/m² | 0.14 MW/m² | 0.06 MW/m² |
| 1,800 °C | 0.70 MW/m² | 0.47 MW/m² | 0.20 MW/m² |
| 2,000 °C | 1.17 MW/m² | 0.78 MW/m² | 0.33 MW/m² |
| 2,200 °C | 1.77 MW/m² | 1.18 MW/m² | 0.50 MW/m² |

Radiation only becomes useful near 2,000 °C, and even there it carries 4–10× less than A2's 3 MW/m² through a wall. It is the only mode in which no material touches both fuel and coolant, which is exactly A2's critical risk.

## The full grid: fuel phase × coolant phase

![Fuel phase by coolant phase grid: condensed fuel with liquid or gas coolant is promising; gas or plasma fuel cannot breed](../assets/figures/fuel-coolant-phase-grid.svg)

Each cell lists the geometries that fit (IDs from the tables above, new ones marked ★) and a verdict for a high-temperature breeder: ● promising · ◐ possible with caveats · ○ unlikely · ✕ ruled out by physics · — not meaningful.

| Fuel ↓ / coolant → | `K-S` solid conduction | `K-P` granular | `K-M` melting carrier | `K-L` liquid | `K-B` boiling / heat pipe | `K-SC` supercritical | `K-G` gas | `K-PL` plasma | `K-R` radiative |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Solid fuel** | ★S7 conduction-cooled monolith ○ (size-limited) | ★S8 particle-cooled pins or blocks ◐ | ○ (carrier melts against cladding: no advantage over liquid) | S1, S2, S3, S6 ● | S3 + heat pipes (B6) ◐; boiling-metal S1 ◐ | S1 with sCO2 ◐ (≤ ~800 °C) | S1, S4, S5, S6 ● | S4 with seeded gas + MHD ○ | ★S9 radiating fuel elements ◐ (needs ≥ ~1,800 °C fuel surface) |
| **Liquid fuel** | — | ○ (particles through fuel: L4 with solid carrier) | ★L4-M melting carrier through fuel ◐ | L1, L2, L3, L5 ● | L4 boiling carrier (X3) ◐ | ○ | L4 gas bubbled through fuel ◐ (carry-over, Pu volatility) | ○ | ★L7 radiatively coupled pool ◐ (chemistry split; large surface) |
| **Gas / plasma fuel** | — | — | — | ✕ (not a breeder) | ✕ | ✕ | G1, G2 ✕ (not a breeder) | G1 seeded propellant ✕ | G2 light bulb ✕ (not a breeder) |

New geometries introduced by the grid:

| ID | Geometry | Idea | Main question |
| --- | --- | --- | --- |
| ★S7 | Conduction-cooled monolith | Fuel in a solid matrix conducting heat to boundary heat pipes or a radiator | Only viable at micro-reactor size; useful as a lower bound of the space |
| ★S8 | Particle-cooled core | Ceramic particles fall through channels between fuel elements, then through an external heat exchanger or storage bin | Heat-transfer coefficient and erosion at 1,000–1,500 °C; particle neutronics (dense, non-moderating ceramics) |
| ★S9 | Radiating fuel elements | Hot solid fuel (UN, UC, cermet) in vacuum or inert gas radiating to cooled tubes | Fuel and container surface ≥ ~1,800 °C for useful flux; emissivity coatings; fission-gas venting |
| ★L4-M | Melting carrier through liquid fuel | Solid carrier pellets (e.g. CaF2, Si) fed into the fuel pool melt, rise and leave as liquid, carrying latent heat | Pellet feeding into a 2,000 °C pool; same carry-over and absorption issues as L4 |
| ★L7 | Radiatively coupled pool | Liquid U–Pu in a refractory container radiating across a gap to aluminium- or lead-cooled walls | Surface needed at 0.3–0.8 MW/m²; container emissivity; gap gas; whether the larger core still breeds |

## Cross-cutting observations

1. **The wall moves, it doesn't disappear.** Solid fuel puts the hottest wall at the fuel surface. Liquid fuel lets the designer choose: inside the core (L2, L3), outside it (L1), or nowhere (L4). That choice drives life-limiting chemistry ([materials selection](../framework/materials-selection.md)).
2. **Fine division kills the fuel's own temperature drop** (table above). Once fuel elements are below ~1 mm, the wall and the coolant set the outlet temperature.
3. **Breeding wants low coolant fraction and dense fuel.** Pins, inverted blocks, pools and liquid-fuel pins keep coolant fractions low. Beds (S4, S5) and direct contact (L4) carry more void or carrier, which costs breeding margin unless the carrier is nearly transparent.
4. **Moving fuel loses delayed neutrons.** Prefer geometries where fuel stays in the core (L2, L3, L4, S1–S4) for plutonium fuel; reserve circulating loops (L1) for uranium-rich or thorium cycles.
5. **Radiative coupling is the only mode with no material touching both fuel and coolant.** It costs surface (0.3–0.8 MW/m² at 2,000 °C), but it removes A2's critical two-fluid wall. It deserves a quantitative check (L7, S9).
6. **Coolant phase trades pressure against heat flux.** Liquids and granular solids run near atmospheric pressure; gases and supercritical fluids need 5–25 MPa; boiling and heat pipes give the highest flux but bring void reactivity.
7. **New candidates worth design pages:** S6 printed lattice, S5 fluidised bed, L3 liquid-fuel pins with diboride or refractory walls, L5 falling film, L7 radiatively coupled pool, and S8 particle-cooled core. Each attacks the heat-path or wall problem differently from the designs already on file.

## Proposed taxonomy axes 11 and 12: core geometry and heat-transport mode

| Code | Geometry |
| --- | --- |
| `S1`–`S6` | Pin bundle · plates · inverted block · packed bed · fluidised bed · printed lattice |
| `L1`–`L6` | Circulating loop · pool with tubes · liquid-fuel pins · direct contact · falling film · rotating annulus |
| `G1`–`G5` | Open gas core · closed gas core · vapour core · fragment conversion · dust suspension |

Axis 11 adds `S7`–`S9`, `L4-M` and `L7` from the grid. Axis 12, heat-transport mode, uses the `K-` codes above; it complements axis 5 (which names the coolant) by saying how heat leaves the fuel.

Existing designs would read (axis 11, axis 12): B1, B2, B5 `S1 K-L`; B3 `S1 K-G`; B4 `L1 K-L`; B6 `S3 K-B`; A1 `S1 K-L`; X1 and A2 `L2 K-L`; X2 `L4 K-L`; X3 `L4 K-B`; A3 `L1 K-L`. Adding both axes is part of [Q-006](../open-questions.md).

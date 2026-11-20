# Study: core geometry by phase of matter

**Status:** ideation (2026-11-20). Nothing here is a design yet; [Q-006](../open-questions.md) asks which geometries to develop into design pages.

Geometry decides how far heat must travel through the fuel, how many walls sit at peak temperature, how much coolant dilutes the core (and so the spectrum and breeding), and whether delayed neutrons stay in the core. This page lists the geometries open to each fuel phase, with what each buys and costs for a high-temperature breeder. The taxonomy so far ([axes 1–10](../framework/taxonomy.md)) records fuel chemistry and coolant but not geometry; a proposed eleventh axis is at the end.

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

## Cross-cutting observations

1. **The wall moves, it doesn't disappear.** Solid fuel puts the hottest wall at the fuel surface. Liquid fuel lets the designer choose: inside the core (L2, L3), outside it (L1), or nowhere (L4). That choice drives life-limiting chemistry ([materials selection](../framework/materials-selection.md)).
2. **Fine division kills the fuel's own temperature drop** (table above). Once fuel elements are below ~1 mm, the wall and the coolant set the outlet temperature.
3. **Breeding wants low coolant fraction and dense fuel.** Pins, inverted blocks, pools and liquid-fuel pins keep coolant fractions low. Beds (S4, S5) and direct contact (L4) carry more void or carrier, which costs breeding margin unless the carrier is nearly transparent.
4. **Moving fuel loses delayed neutrons.** Prefer geometries where fuel stays in the core (L2, L3, L4, S1–S4) for plutonium fuel; reserve circulating loops (L1) for uranium-rich or thorium cycles.
5. **New candidates worth design pages:** S6 printed lattice, S5 fluidised bed, L3 liquid-fuel pins with diboride or refractory walls, and L5 falling film. Each attacks the heat-path or wall problem differently from the designs already on file.

## Proposed taxonomy axis 11: core geometry

| Code | Geometry |
| --- | --- |
| `S1`–`S6` | Pin bundle · plates · inverted block · packed bed · fluidised bed · printed lattice |
| `L1`–`L6` | Circulating loop · pool with tubes · liquid-fuel pins · direct contact · falling film · rotating annulus |
| `G1`–`G5` | Open gas core · closed gas core · vapour core · fragment conversion · dust suspension |

Existing designs would read: B1–B3, B5, A1 `S1`; B4 `L1`; B6 `S3` (block with heat pipes); X1 and A2 `L2`; X2 and X3 `L4`; A3 `L1`. Adding the axis is part of [Q-006](../open-questions.md).

# Project brief

Find, model and pick a reactor concept with three properties at once: it breeds its own fissile fuel with margin (breeding ratio ≥ 1.3), it delivers heat at ≥ 850 °C for > 50% net electric efficiency or direct industrial use, and its core shuts itself down on loss of cooling with no operator action. No reactor has done all three. Regulation, licensing and cost are set aside; physical feasibility is the only test for now.

Figures marked *(approx.)* are literature values from memory, being replaced with sourced values (see [data/claims-check.md](../data/claims-check.md)).

## Mission

Show, through coupled physics models, that a fast breeder can run at ≥ 850 °C core outlet while staying neutronically, chemically and mechanically stable for its whole life. The heat may go to electricity, straight to heavy industry (hydrogen, iron reduction, chemicals, calcination; see [industrial heat](../studies/industrial-heat.md)), or both. Then choose one reference concept for conceptual design.

## Target figures of merit

| Parameter | Baseline target | Stretch target | Today's reference *(approx.)* |
| --- | --- | --- | --- |
| Core outlet temperature | ≥ 850 °C | 1,000–1,200 °C | SFR 500–550 °C; HTR-PM 750 °C |
| Net thermal-to-electric efficiency (electric mode; heat-mode targets in [industrial heat](../studies/industrial-heat.md)) | ≥ 50% | ≥ 55% (combined cycle) | LWR ~33%; SFR ~40% |
| Fissile breeding ratio (BR) | ≥ 1.3 | ≥ 1.5 | Built fast reactors ~1.0–1.3 |
| Compound-system doubling time | ≤ 15 years | ≤ 8 years | Oxide SFR ~20–30 years |
| Burnup per pass | ≥ 15% FIMA | ≥ 25% FIMA | LWR ~5% FIMA; EBR-II/FFTF up to ~20% |
| Uranium utilisation (with recycle) | ≥ 60% | > 95% | Once-through LWR ~0.6% |
| Reactivity feedback | Negative power coefficient; coolant voiding/density worth < 1 βeff | All coefficients negative | EBR-II 1986 unprotected loss-of-flow tests |
| Decay heat removal | Passive: no pumps, no AC power | Passive to an air ultimate sink | PRISM RVACS, BN-800 |
| Primary pressure | ≤ 1 MPa (liquid coolant) | Near-atmospheric | PWR 15.5 MPa; HTGR 7 MPa |
| Life of non-replaceable structures | 40 years | 60 years | LWR 60–80 years |
| Reference thermal power | 1,000 MWth | Scaling study 100–3,000 MWth | — |

## Design premises

Five physical constraints narrow the design space before any modelling:

1. **No moderators in the core.** A fast spectrum rules out hydrogen, beryllium, carbon and lithium-6 except in trace amounts. Every material is checked for moderating power and parasitic capture.
2. **Steels are left behind.** Steels creep at ~550–650 °C. Above 850 °C only nickel superalloys (up to ~900 °C), refractory metals (Mo, Nb, Ta, W) and ceramics (SiC, ZrC, diborides) remain.
3. **The coolant stays single-phase with margin.** Boiling and freezing points at operating pressure bound the usable temperature window.
4. **Breeding wants dense fuel and a hard spectrum.** That favours metal, nitride and carbide fuels, or salts with high actinide content.
5. **Every interface is a chemistry problem.** Fuel–cladding, cladding–coolant, coolant–vessel and coolant–working fluid pairs must each be compatible at peak temperature.

## Modelling domains

| Domain | What is modelled | Key outputs | Tools |
| --- | --- | --- | --- |
| Nuclear data | Evaluated cross sections and covariances, fast range | Group constants, sensitivity coefficients | ENDF/B-VIII.0 (in the [database](../data/database.md)), JEFF-3.3, JENDL-5; NJOY2016 (installed) |
| Neutronics | Transport, criticality, depletion, kinetics | keff, BR, βeff, reactivity coefficients, power maps, dpa, He production | OpenMC 0.16 (installed); Serpent 2, MCNP |
| Chemistry and corrosion | Dissolution, mass transfer, redox, fission-product chemistry | Corrosion rate, deposition, impurity control | Thermochimica, mass-transfer models, CALPHAD |
| Physical properties | Thermal, mechanical and irradiation properties vs temperature and dose | Property database with uncertainties | [htfbr_data](../data/database.md); DFT/MD for gaps |
| Phases of matter | Phase diagrams, melting, boiling, eutectics, decomposition | Operating windows, margins to phase change | NIST-JANAF (in the database), pycalphad, Thermo-Calc, TAF-ID, MSTDB |
| Thermodynamics | Power cycle and heat-transport exergy | Net efficiency, component duties | CoolProp, cycle codes |
| Thermal-hydraulics | Core and loop flow, heat transfer, natural circulation | Peak temperatures, pumping power, decay-heat removal | SAM, RELAP5-3D, NekRS |
| Fuel performance | Swelling, fission-gas release, cladding strain | Burnup limits, failure margins | BISON, TRANSURANUS |
| Coupling | Neutronics ↔ thermal-hydraulics ↔ mechanics | Feedback-consistent steady states and transients | MOOSE, Cardinal |

## Work packages

| WP | Scope | First output (Phase 1) |
| --- | --- | --- |
| WP0 Integration | Requirements, figures of merit, configuration control | Requirements baseline |
| WP1 Neutronics and nuclear data | Core physics, breeding, kinetics, data uncertainty | Infinite-medium screening of all taxonomy branches |
| WP2 Chemistry and corrosion | Compatibility, mass transfer, fission-product chemistry | Pairwise compatibility matrix |
| WP3 Materials properties | Property database, irradiation behaviour | Version-1 database for the long list (started: [database](../data/database.md)) |
| WP4 Phase equilibria | CALPHAD assessments, phase-change margins | Operating windows per candidate |
| WP5 Thermodynamics and thermal-hydraulics | Power cycle, heat transport, passive cooling | Cycle efficiency vs outlet temperature |
| WP6 Fuel performance | Fuel and cladding behaviour to target burnup | Burnup-limiting mechanisms per fuel |
| WP7 Fuel cycle | Mass balance, recycling physics, doubling time | Equilibrium-cycle model |
| WP8 Safety physics | Feedback, transients, decay heat | Unprotected-transient screening |
| WP9 Validation | Benchmarks and experiments needed | Validation gap list |

## Top technical risks

| Risk | Why it matters | Mitigation route |
| --- | --- | --- |
| No structural material qualified for > 100 dpa above ~700 °C | Sets core life and outlet temperature | Replaceable core structures; refractory and ceramic options; temperature split between core and vessel |
| Corrosion and thermal-gradient mass transfer | Hot-leg dissolution, cold-leg plugging | Redox control, coolant purity, inhibitors, solubility-slope criterion in screening |
| Positive coolant void worth in large cores | Can defeat inherent safety | Coolant choice, pancake/leaky geometry, worth limits in screening |
| Low delayed-neutron fraction (Pu-239 β ≈ 0.0021 vs 0.0065 for U-235) | Thin margin to prompt criticality | Strong prompt feedback (Doppler, expansion); control design |
| Fast-range nuclear data gaps (N-15, Cl-37, Pb, Mo, minor actinides) | Uncertain keff and BR | Sensitivity and uncertainty analysis; targeted benchmarks |
| Power conversion above 850 °C | Turbomachinery and heat-exchanger materials | Helium or sCO2 Brayton; ceramic heat exchangers |
| Tritium, helium and activation products | Li coolant makes tritium; Bi makes Po-210; N-14 makes C-14 | Isotope enrichment; screening on activation |

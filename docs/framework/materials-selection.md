# Materials selection method

**Status:** search strategy P1–P7 adopted as a guiding principle ([D-0006](../decisions/D-0006-materials-search-strategy.md)); steps, thresholds and rules proposed, awaiting approval ([Q-005](../open-questions.md)).

This page defines how candidate materials are found and filtered for every component, so the choice is systematic rather than recalled. It covers every material class: pure metals, alloys, intermetallics, ceramics, composites, salts, liquid metals and gases. It is the upstream half of selection. Candidates that survive here go on to the scoring and stack stages in [materials screening](materials-screening.md).

**The core idea.** Most high-temperature failures are chemical: one material reacts with, dissolves into, or forms a low-melting phase with its neighbour. Those outcomes are predictable from thermodynamics before any experiment. The method therefore:

1. starts from what each component must survive;
2. pre-screens the periodic table element by element;
3. builds alloys, compounds and salts only from surviving elements;
4. tests every material against every partner it will touch, with ten explicit chemistry rules.

## The method in six steps

| Step | Question | Output | Tooling |
| --- | --- | --- | --- |
| S1 Component profile | What must this component survive, and what does it touch? | Requirement profile per component and temperature class | This page (table below) |
| S2 Element pre-screen | Which elements are acceptable as major constituents here? | Allowed / penalised / excluded list per component | Property database (absorption, activation, moderation, melting point) |
| S3 Candidate generation | Which materials of each allowed class can be built from those elements? | Candidate list per component, by class | Class matrix below; database species lists; alloy design rules |
| S4 Chemistry rules | Does the candidate survive each partner it touches? | Verdict per pair and rule (R1–R10), with evidence level | JANAF now; CALPHAD, Miedema and salt databases later |
| S5 Physical gates and scoring | Is it good enough, and how good? | Scores with uncertainty | [Screening stages 1–2](materials-screening.md#stage-1-hard-gates) |
| S6 Stacks and robustness | Do whole fuel–cladding–coolant–structure sets work together? | Shortlisted stacks per design | [Screening stages 3–4](materials-screening.md#stage-3-compatibility-stacks) |

Every candidate that reaches S4 gets a [material page](../materials/README.md). Every verdict is recorded with its rule, partner, evidence and source, so a later reviewer can see why something was dropped.

## S1. Component requirement profiles

A profile fixes the temperature window, neutron environment, chemical environment and mechanical duty. Chemistry is judged at the **hot end**; freezing and brittleness at the **cold end**, including shutdown.

| Component | Temperature (by design T class) | Neutron environment | Touches | Mechanical duty |
| --- | --- | --- | --- | --- |
| Fuel | Peak fuel temperature (often 300–800 K above coolant) | Highest flux; fission products | Cladding or container; coolant if liquid fuel | Swelling, fission-gas pressure |
| Cladding / fuel container | Coolant + 50–150 K | High flux, 10–40 dpa/year | Fuel and fission products (inside); coolant (outside) | Hoop stress, creep, thermal stress |
| Coolant / heat carrier | Inlet to outlet | Core flux while in core; activation | Cladding, structures, vessel, heat exchanger, pump | — |
| Core structures | Coolant temperature | High dose, replaceable | Coolant | Creep, swelling, dimensional stability |
| Vessel / primary boundary | Coolant temperature (or ≤ 550 °C in a cold-vessel layout, [Q-003](../open-questions.md)) | Low dose, 40–60 years | Coolant (inside); cover gas or air (outside) | Pressure, creep-fatigue |
| Heat exchanger | Primary hot leg | Low dose | Primary coolant and secondary fluid (two-sided) | Pressure difference, thermal cycling |
| Reflector / shield / absorber | Coolant temperature or higher (gamma heating) | High flux | Coolant or cladding | Swelling |
| Liners, coatings, barriers | As the surface they protect | As located | Both neighbours | Adhesion, thermal mismatch |

## S2. Element pre-screen

Each element is scored as a possible **major constituent** (≥ ~1 wt%) of a material for a given component. Elements that fail can still appear as trace additions or, where they are the point, as functional materials: absorbers, fertile material, enriched isotopes.

| Criterion | Measure | In-core structural / coolant thresholds (provisional) | Source |
| --- | --- | --- | --- |
| Fast-neutron absorption | Natural-element non-fission absorption (MT 101), U-235 fission-spectrum average | ≤ 20 mb acceptable · 20–100 mb penalised · > 100 mb excluded unless isotope-enriched or functional | Database (`v_xs_natural`) |
| Moderation | ξ and atom density | H, Be, graphitic C and Li-6 excluded as major in-core constituents; O, N, C, F allowed in compounds, counted in the moderation budget | Database (ξ from masses) |
| Activation | Half-lives of capture and threshold-reaction products | Flag products with 1 day < T½ < 100 years (e.g. Co-60, Ta-182, Fe-59, Mn-54); exclude only if dominant and unavoidable | Database (LiveChart) |
| Refractoriness | Melting point of element, or of its relevant compounds | Component-specific; see [hard gates](materials-screening.md#stage-1-hard-gates) | JANAF now, SGTE later |
| Isotopic feasibility | Is a needed enrichment achievable (Li-7, N-15, B-11, Cl-37, W-184/186, Pb-206/207)? | Flag cost class; no exclusion at this stage | Registry note |
| Hazard | Toxicity or radiotoxic precursors (Be, Cd, Hg, Tl; Bi → Po-210) | Flag only (physics-first phase) | Registry note |

Thresholds use fission-spectrum averages until averages over real core spectra exist ([Q-011](../open-questions.md)). A real fast core is softer, which lowers the threshold-reaction share and raises resonance capture, so rankings will shift somewhat. Thresholds are therefore bands, not cut-offs.

### Worked example: what the pre-screen already shows

From the database (ENDF/B-VIII.0 via NJOY2016, natural abundances, fission-spectrum average of non-fission absorption):

| Band | Elements (mb) |
| --- | --- |
| ≤ 10 mb | Pb 1.8 · Na 2.4 · Bi 2.7 · V 2.9 · Mn 3.2 · Al 5.2 · Cr 5.3 · Y 5.5 · Ti 6.0 · Co 6.1 · Mg 7.7 · Fe 8.8 · Zr 9.8 |
| 10–40 mb | Si 10.5 · O 11.9 · Li 16.2 · F 16.7 · Cu 25.7 · Sn 27.4 · Nb 27.4 · Mo 33.2 · Be 37.1 |
| 40–100 mb | W 54.9 · Hf 70.5 · Ni 84.8 · Cl 97.8 |
| > 100 mb | Ta 111.5 · N 129.2 · K 145.1 · Ca 146.6 |

Three results contradict earlier from-memory statements in these docs, and show why the pre-screen comes first:

- **Calcium is not a low-absorption element in a fission spectrum.** Ca-40(n,p) contributes ~110 mb and Ca-40(n,α) ~40 mb. Both are essentially zero at thermal energy: they release energy, but the outgoing proton or alpha must escape the nucleus's electric field (the Coulomb barrier), so they only switch on at MeV energies. The penalty for the Ca and CaF2 carriers in [X2](../designs/X2.md) and [X3](../designs/X3.md) therefore depends strongly on how hard the real core spectrum is, and on carrier volume fraction ([Q-023](../open-questions.md)).
- **Nickel (85 mb) costs more than iron (8.8) or chromium (5.3)**, almost all through Ni-58(n,p) (~107 mb for Ni-58), again a MeV-range reaction. That favours Fe- and Cr-based alloys over Ni superalloys inside the core.
- **Natural chlorine (98 mb) and nitrogen (129 mb) are dominated by Cl-35(n,p) and N-14(n,p).** This confirms that chloride fuels need Cl-37 and nitride fuels N-15.

## S3. Candidate generation by class

For each component, only the classes marked in the matrix are generated. Within a class, candidates are built from S2-allowed elements by the rules in the class table.

### Class matrix

| Class | Fuel | Cladding / container | Coolant / carrier | Core structure | Vessel | Heat exchanger | Liner / coating |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pure refractory metals | — | ● | — | ● | ○ | ○ | ● |
| Alloys (solid-solution, ODS, precipitation) | ● metallic fuel | ● | — | ● | ● | ● | ○ |
| Intermetallics and MAX phases | — | ○ | — | ○ | — | ○ | ● |
| Oxides | ● | ○ | — | ○ | — | — | ● |
| Carbides, nitrides, borides, silicides | ● | ● | — | ● | — | ● | ● |
| Ceramic composites (SiC/SiC) and cermets | ● cermet fuel | ● | — | ● | — | ● | — |
| Halide salts and their mixtures | ● fuel salt | — | ● | — | — | — | — |
| Liquid metals and liquid alloys | ● liquid fuel | — | ● | — | — | — | ○ bond layers |
| Gases | — | — | ● | — | — | — | — |

● generate candidates · ○ generate only for a stated reason · — not applicable.

### How each class is generated

| Class | Generation rule | What governs it chemically | Typical traps |
| --- | --- | --- | --- |
| **Alloys** | Start from an allowed base metal. Add an alloying element only for a stated purpose (strength, oxidation resistance, ductility, grain stability), and only if it passes S2. Include qualified commercial alloys as reference points (316H, T91, Alloy 617, Haynes 230, Hastelloy N, ODS FeCrAl, TZM, Nb-1Zr, Ta-10W, W-Re). | Phase stability across the temperature range (CALPHAD); selective attack on the least noble or most soluble major element (rule R6) | Embrittling phases (sigma, Laves, α′ in Fe-Cr near 475 °C); radiation-induced segregation; a 1% addition that is incompatible with the coolant |
| **Intermetallics and MAX phases** | Aluminides (NiAl, FeAl), silicides (MoSi2), MAX phases (Ti3SiC2, Ti2AlC, Cr2AlC) as coatings or claddings where a protective scale is wanted | Protective-scale formation (Al2O3, SiO2) and its stability in the environment | Brittleness; scale unstable in reducing liquid metals or salts |
| **Ceramics** (oxides, carbides, nitrides, borides) | Binary compounds of allowed metals with O, C, N, B, Si; ternaries only when a binary fails for a known reason | Exchange reactions with partners (R1); decomposition and volatility (R4) | Moderating anions (counted against the budget); B-10 and N-14 unless enriched |
| **Composites and cermets** | SiC/SiC; refractory-metal-matrix fuels (UN–W, UN–Mo) | Interface reactions between matrix and reinforcement (R1, R3) | Fibre/matrix degradation under irradiation |
| **Halide salts** | Fluorides or chlorides only; mixtures chosen to lower the melting point (eutectics) | Cation stability, redox control, actinide solubility, vapour pressure (R9) | Nitrates (decompose above ~600 °C), carbonates (above ~800 °C, need CO2 cover), hydroxides and sulfates are excluded for the hot core |
| **Liquid metals** | Pure metals and eutectics of allowed elements (Pb, Pb-Bi, Na, Na-K, Li-7, Sn, Al, Ga); liquid fuels (U-Pu, U-Pu-Cr) | Solubility of container elements and intermetallic formation (R2); mass transfer (dS/dT) | Selective leaching of Ni, Fe or Cr from alloys; oxygen and nitrogen impurities |
| **Gases** | He, N2, CO2, Ar (Ar activates) | Impurity-driven oxidation, carburisation and nitridation (R5) | Ni alloys carburise or decarburise at ppm CO/H2O |

## S4. Chemistry rules

Each candidate is checked against each partner it touches at the hot-end temperature. A rule returns **compatible**, **conditional** (works only with a stated control: a coating, a redox or oxygen window, an impurity limit), or **incompatible**. The weakest rule decides.

| Rule | Question | Method (in order of preference) | Default margin |
| --- | --- | --- | --- |
| **R1 Exchange reactions** | Will A take the anion (O, N, C, B, F, Cl) from compound BX? | Compare ΔfG°(AX) with ΔfG°(BX) per mole of the shared reactant (O2, N2, C, F2, Cl2) at temperature: the generalised Ellingham comparison. In solutions, correct with activities. | Compatible if the compound in place is more stable by ≥ 40 kJ per mol of reactant; within ±40 kJ is conditional |
| **R2 Liquid-metal attack and liquid–liquid miscibility** | Does a liquid metal dissolve or form compounds with the solid? Do two liquids stay separate? | Binary phase diagram (intermetallics, solubility at T, miscibility gap and its consolute temperature); if none, Miedema enthalpy of mixing as a screen (strongly negative = attack; positive = immiscible); then solubility slope dS/dT for mass transfer. Miscibility gaps narrow and close as temperature rises, and "immiscible" never means zero solubility: always state the temperature and the mutual solubility | Incompatible if intermetallics form or solubility at T > ~0.1 at%; conditional if inhibitor or oxygen control required |
| **R3 Low-melting phases** | Do the two form a eutectic or liquid below the hot end + 100 K? | Binary and ternary phase diagrams (CALPHAD) | Incompatible if any liquid forms below peak + 100 K |
| **R4 Volatility and decomposition** | Does the material, or a reaction product, evaporate or decompose? | Vapour pressure of all species (including volatile oxides MoO3 and WO3, halides AlCl3 and UF6, suboxides Al2O and SiO) and decomposition pressure (UN, AlN, carbonates) | Conditional above 10⁻⁶ bar; incompatible above 10⁻³ bar at the hot end, unless designed for |
| **R5 Gas–solid** | Do coolant or cover-gas impurities oxidise, nitride or carburise the solid? | Oxygen, nitrogen and carbon potential windows from JANAF; known behaviour for He and CO2 environments | Conditional with a stated impurity limit |
| **R6 Selective leaching (alloys)** | Which alloying element is attacked first? | Apply R1 and R2 to every major element (≥ ~1 wt%) separately. The alloy is rated by its worst major element unless a stable, self-healing protective layer exists. | Worst element sets the verdict |
| **R7 Protective layers** | Is a scale or coating doing the work? | Scale must be thermodynamically stable in the environment (R1, R5) and able to re-form; a coating's defects must be tolerable | Always conditional, never compatible |
| **R8 Transmutation and fission products** | Does irradiation change the chemistry? | List products: W → Re, Os; B-10 → Li + He; Cl-35 → S; N-14 → C-14; Al → Si, Mg; fuel-side Cs, Te, I attack on cladding. Re-apply R1–R3 to the new elements. | Flag; incompatible if the product creates a liquid or brittle phase within design life |
| **R9 Salt chemistry** | Is a salt stable, non-corrosive and fit as fuel or coolant? | Cation stability (ΔfG° per mol F2 or Cl2): structural metals must form much less stable halides than the salt's cations. Redox control (e.g. U(IV)/U(III) ratio). Actinide solubility, melting point of the mixture, vapour pressure, cation neutronics (Li-7, Na, K, Ca, Mg, Zr; Cl-37). | Container metals compatible if their halides are less stable than the salt by ≥ 40 kJ per mol F2/Cl2, given the redox window |
| **R10 Alloy phase stability** | Does the alloy stay single- or designed-phase over the temperature range and dose? | CALPHAD; known embrittlement windows; radiation-induced segregation literature | Incompatible if an embrittling phase forms in the operating window |

**Evidence levels**, used as "data confidence" in [scoring](materials-screening.md#stage-2-figures-of-merit):

| Level | Basis |
| --- | --- |
| E1 | Measured in the actual environment (temperature, chemistry, irradiation) |
| E2 | Measured in the environment without irradiation, or a close analogue |
| E3 | Assessed thermodynamic database (JANAF, SGTE, CALPHAD, MSTDB) |
| E4 | Estimate (Miedema, DFT, analogy) |
| E5 | Expert judgement or memory |

A verdict at E4–E5 cannot move a candidate past S6 on its own; it creates an open question.

### How the rules apply to salts and alloys: two examples

- **Nickel alloy in a fluoride salt** (R9, R6). Nickel, molybdenum and tungsten fluorides are much less stable than LiF, NaF or BeF2, so those metals are compatible. Chromium is not: Cr + 2UF4 → CrF2 + 2UF3 proceeds unless the U(IV)/U(III) ratio is kept low. So a Ni-Mo-Cr alloy is rated by its chromium (R6). That is why the molten-salt experiments of the 1960s used Hastelloy N, a nickel alloy with only ~7% Cr, plus redox control.
- **Steel or nickel alloy in liquid lead** (R2, R6, R7). Nickel dissolves strongly in lead, iron less, chromium in between. A steel survives only if dissolved oxygen keeps an iron–chromium oxide scale stable (R7, conditional, ≤ ~550 °C). An alumina-forming FeCrAl alloy has a more stable scale. Molybdenum, tungsten and SiC barely dissolve and are compatible without a scale.

## Guiding principle: search without enumerating, reject only on evidence

**Adopted 2026-11-20 ([D-0006](../decisions/D-0006-materials-search-strategy.md)).** These seven rules govern how every step above is applied. Their purpose is to keep the search tractable while making the risk of discarding a good combination very low.

The raw space explodes. 7 component slots × ~50 candidates is ~10¹² combinations, before isotopes, temperature and pressure. So the space is never enumerated, and every elimination step is one-sided: it removes only what fails even under favourable assumptions.

| # | Principle | How it is applied |
| --- | --- | --- |
| P1 | **Most constraints are pairwise.** | Chemistry is checked per touching pair (~10 pairs per design, ~10 × 50² ≈ 25,000 checks), not per full combination. Only whole-design properties (neutron budget, temperature chain) are checked on the full set, and only on survivors. |
| P2 | **Continuous variables are intervals, not grids.** | Degradation mechanisms (corrosion, vapour pressure, solubility, creep) worsen with temperature, so a pair is tested at the hot end of its window. A failure triggers a search for the highest workable temperature. Each pair yields an operating window; windows from different pairs are intersected. Pressure is treated the same way. |
| P3 | **Design choices are screened at their best case.** | Isotopic enrichment is assumed at its best achievable level (Li-7, N-15, B-11, Cl-37, W-184/186, Pb-206/207); its cost is weighed later in scoring. |
| P4 | **Element-level pruning only where it is exact.** | Additive properties (absorption, activation) prune at element level: if an element's share alone breaks the budget, every material with that share fails. Chemistry is not additive (compounds can be more stable than their elements; scales can protect), so element results only flag; the actual alloy or compound is still tested. |
| P5 | **Constraint propagation, not enumeration.** | A design is a set of slots with unary gates, pairwise rules and global budgets. A candidate with no compatible partner left in a neighbouring slot is removed, and removals cascade. Only consistent partial designs are ever explored. |
| P6 | **Asymmetric error control: wrong rejections are the costly error.** | Rejection requires evidence E1–E3; E4–E5 can only mark a pair conditional. Margins sit on the generous side. Every rejection is recorded (rule, evidence, source) and re-screened automatically when data change. Each run is repeated with relaxed thresholds (margins halved, absorption bands widened); what reappears goes on a near-miss list for human review. The rules must pass the [calibration cases](#calibration-cases). |
| P7 | **Cheap checks first; several survivors per branch.** | Fidelity ladder: element tables → JANAF stability → CALPHAD phase diagrams → infinite-medium neutronics → 3D Monte Carlo. Each stage is roughly 10× costlier per option and sees roughly 10× fewer options. Three to five survivors are kept per branch, never a single winner. |

### Calibration cases

Combinations that have worked in real reactors or long loop tests. The rules must not reject any of them under their real conditions. A rule that would is wrong and must be fixed before it is used. They are listed in `config/calibration_cases.yaml` and become automated tests when the compatibility rules are coded.

| Case | Conditions | Why it works | Rules exercised |
| --- | --- | --- | --- |
| Sodium with 316 stainless steel | ~550 °C, low oxygen | Low solubility of Fe, Cr, Ni in Na at this temperature | R2, R5 |
| Hastelloy N in fluoride salt (LiF-BeF2 based) | ~650–700 °C, U(IV)/U(III) redox control | Ni and Mo fluorides far less stable than the salt; Cr kept low (~7%) and its leaching limited by redox | R9, R6 |
| T91 / ferritic-martensitic steel in lead or lead-bismuth | ≤ ~550 °C, dissolved-oxygen control | Protective Fe-Cr oxide scale | R2, R6, R7 |
| Nb-1Zr with lithium (SP-100 class) | ~1,000–1,100 °C, ppm oxygen in Nb | Refractory metal with low solubility in Li; oxygen controlled | R2, R5 |
| Alloy 617 in helium | ~850–950 °C, ppm impurity control | Impurity-controlled oxidation and carburisation | R5, R7 |
| Molten uranium under CaF2 slag | ~1,400–1,600 °C, short contact (metallothermic U production) | Metal–salt immiscibility; CaF2 more stable than U fluorides | R1, R2 |

Some conditions are given as approximate ranges; they will be pinned to sourced values when the cases are coded.

## Records and tooling

| Record | Where | Status |
| --- | --- | --- |
| Component profiles | This page (S1) | Done |
| Element pre-screen table per component | Generated report from the database | To build: database has absorption, activation and ξ |
| Candidate list per component and class | `docs/materials/` pages plus the [long list](materials-screening.md#initial-long-list) | Partial; to be regenerated by class |
| Pairwise verdicts (rule, partner, temperature window, verdict, evidence level, source) | `config/compatibility.yaml`, rendered into a compatibility matrix page and into each material page | To build |
| Calibration cases (P6) | `config/calibration_cases.yaml`; automated tests once the rules are coded | Cases listed; tests to build |
| Rejection log and near-miss report (P6) | Generated on every screening run | To build |
| R1 exchange-reaction calculator | `htfbr_data` (JANAF ΔfG° at temperature, per mole of reactant) | To build: JANAF data already loaded |
| Phase diagrams and alloy stability (R3, R10) | pycalphad with open databases; licensed databases where needed | To set up |
| Liquid-metal screen (R2) | Miedema estimator plus literature solubility entries | To build |
| Salt properties (R9) | ORNL MSTDB-TP/TC (registration needed) plus JANAF | Blocked: needs access |

## What this changes in the current docs

- The [Ca](../materials/calcium.md) and [CaF2](../materials/calcium-fluoride.md) carriers ([X2](../designs/X2.md), [X3](../designs/X3.md)) now carry an absorption penalty to quantify ([Q-023](../open-questions.md)).
- In-core alloys should be generated Fe- and Cr-based first; Ni-based alloys are penalised in core but remain candidates for vessels and heat exchangers outside the core.
- Each material page gains a "Chemistry checks" table (rule × partner) once `config/compatibility.yaml` exists.

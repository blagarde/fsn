# Design taxonomy

Each candidate gets one value on each of ten independent axes. The resulting designation string lets any two concepts be compared axis by axis, and lets the design space be counted, pruned and searched. Every page in [designs/](../designs/README.md) carries its designation in its header.

## Axes and codes

| # | Axis | Code | Classes |
| --- | --- | --- | --- |
| 1 | Fuel phase and chemistry | F | `S-O` oxide · `S-C` carbide · `S-N` nitride · `S-M` metal alloy · `S-K` cermet / composite · `S-P` coated particle · `L-Cl` chloride salt · `L-Fl` fluoride salt · `L-M` liquid-metal fuel · `G` gas or vapour core |
| 2 | Fuel cycle | Y | `UPu` U-238 → Pu-239 · `ThU` Th-232 → U-233 · `MX` mixed or transmuting · `U` non-breeding reference |
| 3 | Breeding arrangement | B | `I` integral core, no blankets · `A` axial and radial blankets · `H` heterogeneous, internal blankets · `W` breed-and-burn wave · `X` separate fertile stream |
| 4 | Spectrum hardness | N | `H` hard, median neutron energy > ~200 keV · `F` standard fast, ~100–200 keV · `E` intermediate, < 100 keV |
| 5 | Primary coolant | C | `Na` · `NaK` · `K` · `Li7` · `Pb` · `PbBi` · `Sn` · `Al` aluminium · `He` · `CO2` · `ClS` chloride salt · `FlS` fluoride salt · `HP` heat pipes (working fluid noted) · `Self` liquid fuel is the coolant · `DC-x` direct-contact carrier x passed through liquid fuel |
| 6 | Core outlet temperature | T | `T1` < 550 °C · `T2` 550–750 °C · `T3` 750–950 °C · `T4` 950–1,200 °C · `T5` > 1,200 °C |
| 7 | Primary pressure | P | `L` < 1 MPa · `M` 1–5 MPa · `H` > 5 MPa |
| 8 | Primary architecture | A | `Lp` loop · `Po` pool · `In` integral, heat exchangers in vessel · `Mo` monolith / heat-pipe block |
| 9 | Power conversion | E | `R` Rankine · `B-He`, `B-N2`, `B-CO2` Brayton · `CC` combined cycle · `D-x` direct conversion (TI, TE, AM, MHD, FF) · `PH-x` process heat, x = use-case code from [industrial heat](../studies/industrial-heat.md) · `CG` cogeneration |
| 10 | Fuel management | M | `Ba` batch reload · `On` online processing (liquid fuel) · `Re` continuous recirculation · `Sh` in-core shuffling |

Secondary attributes (reactivity control, passive shutdown features, decay-heat sink) are recorded on design pages but do not define a branch.

**Designation format:** `F | Y | B | N | C | T | P | A | E | M`, for example `S-N | UPu | A | H | Pb | T3 | L | Po | B-He | Ba`.

## Exclusion rules

Physics rules out some combinations before scoring, pruning ~10⁷ raw combinations to a few thousand:

1. **Boiling margin.** Coolant boiling point at system pressure must exceed peak coolant temperature by ≥ ~300 K. Na, NaK and K are limited to T1–T2 at low pressure ([D-0001](../decisions/D-0001-no-sodium-branch.md)).
2. **Freezing margin.** Coolant or fuel-salt melting point ≥ ~50 K below the minimum (inlet) temperature.
3. **Spectrum consistency.** FlS, Li-6 or any hydride/graphite content forces N = E. N = H requires F in {S-M, S-N} with a heavy coolant.
4. **Gas pressure.** C in {He, CO2} forces P = H.
5. **Liquid fuel.** F = L-x forces C = Self, DC-x, or an in-vessel exchanger, and M = On.
6. **Breed-and-burn.** B = W requires N = H and heavy-metal density ≥ ~12 g/cm³.
7. **Fuel temperature.** S-M fuel (solidus ~1,100–1,200 °C, Fe eutectic ~650–725 °C) is excluded above T2 unless clad in a non-ferrous refractory metal.
8. **Breeding mandate.** Y = U is allowed only as a comparison reference.

## Known reactors classified

| Reactor | Designation | Note |
| --- | --- | --- |
| EBR-II (US, 1964–94) | `S-M \| UPu \| A \| H \| Na \| T1 \| L \| Po \| R \| Ba` | Passive-safety demonstration in 1986 |
| BN-800 (Russia) | `S-O \| UPu \| A \| F \| Na \| T1 \| L \| Po \| R \| Ba` | Operating oxide/MOX SFR |
| BREST-OD-300 (Russia) | `S-N \| UPu \| I \| H \| Pb \| T1 \| L \| Po \| R \| Ba` | BR ≈ 1 by design |
| Gen IV GFR reference | `S-C \| UPu \| I \| F \| He \| T3 \| H \| Lp \| CC \| Ba` | Concept |
| MSFR (Euratom concept) | `L-Fl \| ThU \| X \| F \| Self \| T2 \| L \| In \| B-He \| On` | Fast because fuel salt is ~20 mol% heavy metal |
| MCFR (TerraPower concept) | `L-Cl \| UPu \| I \| F \| Self \| T2 \| L \| In \| R \| On` | Chloride fast reactor |
| TWR (TerraPower concept) | `S-M \| UPu \| W \| H \| Na \| T1 \| L \| Po \| R \| Sh` | Breed-and-burn |
| SP-100 (US space, cancelled) | `S-N \| U \| I \| H \| Li7 \| T4 \| L \| Lp \| D-TE \| Ba` | High-temperature fast-spectrum precedent |

Project designs and their designations are listed in the [design index](../designs/README.md).

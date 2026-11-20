# Designs

One page per candidate design. The table is generated from each page's front matter by `htfbr-data docs`; to add a design, copy [the template](_template.md). Designations follow the [taxonomy](../framework/taxonomy.md); status values are explained in the [documentation map](../README.md#conventions).

**Families:** `B` seed branches from the Phase 0 taxonomy · `X` liquid U–Pu fuel at ~2,000 °C ([study](../studies/liquid-fuel-2000c.md)) · `A` aluminium-cooled ([study](../studies/aluminium-coolant.md)).

<!-- BEGIN GENERATED design-index -->
12 designs: 8 seed, 3 exploring, 1 analysed.

| ID | Design | Status | Outlet (°C) | Fuel | Coolant | Boundary | Key risk | Designation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [A1](A1.md) | Solid nitride fuel, aluminium-cooled | seed | 1200-1600 | (U,Pu)N pins with N-15 | Al (near-atmospheric) | ZrB2 (B-11) cladding, or W with an AlN outer layer | Brittle ceramic cladding under fission-gas pressure | `S-N \| UPu \| A \| H \| Al \| T5 \| L \| Po \| CC \| Ba` |
| [A2](A2.md) | Liquid U-Pu pool cooled by aluminium | analysed | 1700-1880 | Liquid U-Pu metal at ~2,000 °C, stationary pool | Al (~0.05 bar at 2,000 °C, database) | W/AlN duplex tube wall (reference); monolithic ZrB2 (B-11) alternative; Pb-bonded double wall as mitigation | No tube wall proven against liquid U and liquid Al at ~2,000 °C and 10-15 dpa/year | `L-M \| UPu \| A \| H \| Al \| T5 \| L \| In \| CC \| On` |
| [A3](A3.md) | Al-U-Pu solution fuel | seed | 1600-2000 | U and Pu dissolved in circulating liquid Al | Self (fuel solution) | none between fuel and coolant; containment from the Al-compatible list | Low heavy-metal density and softer spectrum; delayed neutrons swept out of the core | `L-M \| UPu \| A \| F \| Self \| T5 \| L \| Lp \| CC \| On` |
| [B1](B1.md) | Lithium-cooled nitride | seed | 950-1200 | (U,Pu)N with N-15 | Li-7 (> 99.9%) | Refractory-metal cladding (Nb-1Zr, Mo, Ta alloys) | Tritium production from lithium; refractory-metal embrittlement and oxygen control | `S-N \| UPu \| A \| H \| Li7 \| T4 \| L \| Lp \| CC \| Ba` |
| [B2](B2.md) | Lead-cooled nitride | seed | 750-950 | (U,Pu)N with N-15 | Pb | Cladding to be chosen (steels limited to ~550 °C in Pb) | Corrosion of cladding and structures in lead above ~550 °C | `S-N \| UPu \| A \| H \| Pb \| T3 \| L \| Po \| B-He \| Ba` |
| [B3](B3.md) | Helium-cooled carbide or nitride | seed | 950-1200 | (U,Pu)C or (U,Pu)N | He at ~7 MPa | Ceramic or refractory cladding (SiC/SiC candidates) | Passive decay-heat removal with a low-density gas coolant | `S-C \| UPu \| H \| F \| He \| T4 \| H \| Lp \| CC \| Ba` |
| [B4](B4.md) | Chloride fuel salt | seed | 750-950 | NaCl-UCl3-PuCl3 with Cl-37 | Self (fuel salt) | Vessel and heat exchanger alloys (Mo-based or Ni alloys) | Salt volatility and corrosion at T3; Cl-37 enrichment | `L-Cl \| UPu \| I \| F \| Self \| T3 \| L \| In \| CC \| On` |
| [B5](B5.md) | Lead-cooled cermet | seed | 950-1200 | UN-W or UN-Mo cermet | Pb | Cermet matrix (W or Mo) as fission-product barrier | Neutron absorption in the W or Mo matrix; lead corrosion of structures at T4 | `S-K \| UPu \| A \| H \| Pb \| T4 \| L \| Po \| CC \| Ba` |
| [B6](B6.md) | Heat-pipe monolith | seed | 950-1200 | (U,Pu)N | Lithium heat pipes | Refractory-metal heat-pipe walls | Size limit of heat-pipe cores; tritium from lithium | `S-N \| UPu \| A \| H \| HP(Li) \| T4 \| L \| Mo \| CC \| Ba` |
| [X1](X1.md) | Liquid U-Pu pool, lead behind tungsten tubes | exploring | 1800-1900 | Liquid U-Pu metal at ~2,000 °C | Pb (~3 bar at 2,000 °C) | W or W-Re tube wall | W creep and embrittlement at 2,000 °C; U-W mass transfer on the fuel side | `L-M \| UPu \| A \| H \| Pb \| T5 \| L \| In \| CC \| On` |
| [X2](X2.md) | Liquid U-Pu pool, CaF2 direct contact | exploring | 1800-1900 | Liquid U-Pu metal at ~2,000 °C | Molten CaF2 droplets (~0.04 bar at 2,000 °C) | none (direct contact, density separation) | Fuel droplets carried out in the salt; fission-product exchange | `L-M \| UPu \| A \| H \| DC-CaF2 \| T5 \| L \| Po \| CC \| On` |
| [X3](X3.md) | Liquid U-Pu pool, boiling calcium direct contact | exploring | 1800-1900 | Liquid U-Pu metal at ~2,000 °C | Boiling Ca (~9 bar at 2,000 °C, database extrapolation) | none (direct contact, boiling) | Void reactivity from Ca vapour; U and Pu solubility in Ca at 2,000 °C unknown | `L-M \| UPu \| A \| H \| DC-Ca \| T5 \| M \| Po \| CC \| On` |

**By family:** Aluminium coolant: [A1](A1.md), [A2](A2.md), [A3](A3.md) · Seed branches (Phase 0 taxonomy): [B1](B1.md), [B2](B2.md), [B3](B3.md), [B4](B4.md), [B5](B5.md), [B6](B6.md) · Liquid fuel at ~2,000 °C: [X1](X1.md), [X2](X2.md), [X3](X3.md)
<!-- END GENERATED -->

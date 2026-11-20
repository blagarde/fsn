# State of the art and theoretical efficiency limits

Today's power reactors turn 31–41% of their heat into electricity. Outlet temperature sets that figure, and materials cap the temperature; fission itself does not. Three ceilings matter for this project: ~96% of fission energy can be recovered as heat, the Carnot limit at the outlet temperature caps conversion, and η − 1 caps breeding.

Figures are *(approx.)* literature values unless tagged with a database source. The efficiency-versus-temperature chart is in the Claude Doc (Master plan, section 2.2).

## Where fission energy goes

| Component (U-235 fission) | Energy (MeV, approx.) | Recovered as heat |
| --- | --- | --- |
| Fission-fragment kinetic energy | ~169 | Yes, deposited within ~10 µm in the fuel |
| Prompt gamma rays | ~7 | Yes, in fuel, coolant and structures |
| Prompt neutron kinetic energy | ~5 | Yes, mostly in coolant and structures |
| Beta decay of fission products | ~6.5 | Yes, as decay heat |
| Delayed gamma rays | ~6.3 | Yes, as decay heat |
| Antineutrinos | ~8.8 | No, they escape |
| Capture gammas from non-fission absorptions | +3 to 12 | Yes, extra heat |

Net recoverable heat is ~193–200 MeV per fission (Pu-239: ~207 MeV released), ~0.09% of the fissioned mass: the absolute ceiling of fission as an energy source.

## Thermodynamic ceilings

```
η_Carnot = 1 − Tc/Th        η_CA (Curzon–Ahlborn, max power) = 1 − √(Tc/Th)
```

Built plants reach 57–69% of their Carnot limit and sit near the Curzon–Ahlborn curve. At 850–1,200 °C that curve gives 48–55%, so a 50% target needs a high-temperature Brayton cycle, a combined cycle, or both. At ~2,000 °C (see [liquid fuel](../studies/liquid-fuel-2000c.md)) Carnot is 87% and Curzon–Ahlborn 64%.

Fuel melting is not the temperature limit (UO2 ~2,865 °C, UN ~2,850 °C under N2 overpressure). The limits are cladding and structural creep (steels ~550–650 °C), coolant boiling, and corrosion rates, which roughly double every 20–50 K.

Routes past a single cycle:

- **Combined cycle** (helium or N2 Brayton topping, steam bottoming): ~55–60% at 1,100–1,300 °C turbine inlet.
- **Supercritical CO2 Brayton**: ~50% at 700–750 °C turbine inlet.
- **Direct conversion**: thermionic (TOPAZ, ~5–10%), thermoelectric (SP-100 design, ~4–6%), AMTEC (~15–20% lab), MHD. Topping stages only.
- **Fission-fragment direct conversion**: fragments carry ~1 MeV per nucleon of non-thermal energy, so Carnot does not apply; 50–90% proposed, nothing near power scale. Long-range option only.

## State of the art by reactor class

About 415 power reactors (~375 GWe) operate worldwide, nearly all thermal-spectrum water reactors. Fast-reactor experience is ~400 reactor-years, mostly sodium-cooled.

| Class | Reference plants | Spectrum | Coolant / fuel | Status (approx., 2026) | Relevance |
| --- | --- | --- | --- | --- | --- |
| PWR / BWR / PHWR | Global fleet | Thermal | Water / UO2 | ~90% of world capacity | Efficiency baseline only |
| AGR | Torness, Heysham | Thermal | CO2 / UO2 in steel | Fleet retiring | Gas-cooled 640 °C experience |
| HTGR | HTR-PM (China) | Thermal | Helium / TRISO | Commercial since 2023 | Helium Brayton and high-temperature components |
| SFR | EBR-II, Phénix, BN-600, BN-800, CFR-600, PFBR | Fast | Sodium / oxide or metal | Operating in Russia and China; PFBR commissioning | Breeding, metal fuel, passive safety; capped by Na boiling |
| LFR | BREST-OD-300; Alfa-class submarine reactors (Pb-Bi) | Fast | Lead or Pb-Bi / nitride | BREST under construction | Nitride fuel; high boiling margin |
| Fast MSR | MSFR, MCFR concepts; MSRE (thermal, 1965–69) | Fast | Chloride salt with dissolved fuel | Experiments planned | Liquid fuel, online processing |
| GFR | ALLEGRO, EM2 concepts | Fast | Helium / carbide or nitride | Concept only | Highest outlet temperature among fast designs |
| Space fast reactor | SP-100, SNAP-50, Kilopower | Fast | Li-7 or heat pipes / UN or U-Mo | SP-100 cancelled 1994; KRUSTY test 2018 | UN + Nb-1Zr + Li-7 at ~1,075 °C: closest precedent for our range |
| Liquid metal fuel | LAMPRE (Los Alamos, 1961–63); BNL LMFR design (1950s) | Fast / thermal | Molten Pu–Fe in Ta; U dissolved in Bi | Historical | Precedents for [X1–X3](../designs/README.md) and [A3](../designs/A3.md) |

## Breeding limits

Uranium utilisation is ~0.6% for once-through LWRs and can exceed 95% with breeding and full recycle.

```
BR_max ≈ η + ε − 1 − L            t_D ≈ M_fissile / ((BR − 1) · ṁ_fissile)
```

| Fissile isotope | η, thermal (0.025 eV) | η, fast spectrum (approx.) | β (delayed fraction) |
| --- | --- | --- | --- |
| Pu-239 | 2.11 | 2.4 (oxide) to 2.9 (very hard) | 0.0021 |
| U-233 | 2.29 | ~2.3 | 0.0026 |
| U-235 | 2.07 | ~2.1 | 0.0065 |

With ε ≈ 0.2–0.3 and L ≈ 0.2–0.4, the U–Pu cycle in a hard spectrum allows BR up to ~1.6–1.8; 1.3–1.5 is realistic. Thermal Th–U233 breeders reached only ~1.01–1.06. Achieved doubling times are 20–30 years for oxide SFRs, possibly 10–15 years with metal or carbide fuel. 1% FIMA ≈ 9.5 GWd/tHM.

**Implication:** a hard spectrum and dense fuel give the BR margin; outlet temperature gives the efficiency. The two conflict mainly through materials, which is why [materials screening](../framework/materials-screening.md) is central.

# Family X screening (liquid U-Pu metal fuel at ~2,000 °C)

Phase 1 screening of X1 (Pb behind W tubes), X2 (CaF2 direct contact) and X3 (boiling Ca direct contact). Results feed [docs/studies/x-family-screening.md](../../docs/studies/x-family-screening.md).

## Rerun

```bash
export PATH=/opt/mamba/envs/nuc/bin:$PATH
cd /home/user/fsn
python analysis/x-family/thermo_chem.py   # database facts -> results/thermo_chem.json  (seconds)
python analysis/x-family/thermal.py       # 1D sizing + cycle -> results/thermal.json     (seconds)
python analysis/x-family/neutronics.py    # OpenMC infinite medium -> results/neutronics.json
```

`neutronics.py` needs `data/openmc/cross_sections.xml` and caches every OpenMC run in `results/runs/<label>.json`; delete a file to rerun that case (about 1–3 min each with 1 thread, 20,000 particles × 60 batches, 20 inactive). Order matters: `thermal.py` reads `thermo_chem.json`, `neutronics.py` reads the X1 reference volume fractions from `thermal.json`.

## Files

| File | Content |
| --- | --- |
| `thermo_chem.py` | Read-only database pulls: carrier vapour pressures and saturation temperatures, Ca latent heat, liquid cp, CaF2 ΔfG per mol F2, melting points (JANAF, SGTE), per-isotope fast absorption (ENDF/B-VIII.0) |
| `thermal.py` | X1 tube-bundle sizing (Pb film, W wall, fuel conduction), X2 droplet-column holdup and power per pool area, X3 boiling-column void and power per pool area, Carnot / Curzon–Ahlborn / combined-cycle estimates |
| `neutronics.py` | k∞, conversion-ratio proxy, median flux energy and parasitic absorbers for fuel alone and each design; carrier volume-fraction sweeps; void, Doppler (1,200 vs 2,100 K) and isotope cases |
| `results/*.json` | Outputs; `results/runs/` per-run OpenMC summaries |

## Main assumptions (approx.)

- Liquid U–Pu 16.4 g/cm³, Pb 8.7, W 19.0, CaF2 2.4, liquid Ca 1.2 g/cm³; Ca vapour 1.95 kg/m³ (9.2 bar, 2,000 °C, ideal gas from database vapour pressure).
- Reactor-grade Pu vector (approx.): Pu-238/239/240/241/242 = 2/60/24/9/5 at%; depleted U, 0.25% U-235. Pu fraction is atom Pu/(U+Pu).
- Neutronics at 2,100 K (top of the library). The design fuel temperature (~2,000–2,100 °C, 2,270–2,370 K) is above it; Doppler is extrapolated from 1,200–2,100 K.
- Infinite homogeneous medium: no leakage (target k∞ = 1.15), no self-shielding between fuel and carrier, no blanket. Void in an infinite medium only acts through the removed material; the leakage part of a pool void is a one-group estimate.
- Thermal: 1,000 MWth, peak fuel 2,100 °C, local-to-average 1.3; property values listed in `thermal.py` (`PROPS`).

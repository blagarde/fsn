# htfbr-data

Provenance-tracked property database for the HT-FBR design study. Every number traces to a
registered source, and every fetched number to the exact raw file (URL, zip member, SHA-256,
retrieval time) it was parsed from.

## Quick start

```bash
bash setup/install_env.sh                 # micromamba env "nuc": Python 3.12, NJOY2016, OpenMC 0.16 (conda-forge)
export PATH=/opt/mamba/envs/nuc/bin:$PATH
htfbr-data build                          # registry + LiveChart + JANAF + manual CSVs + ENDF processing
htfbr-data check                          # compare figures in the design doc with the database
htfbr-data status
htfbr-data sql "SELECT * FROM v_xs_natural WHERE symbol='Al' AND mt=102"
```

`htfbr-data build --no-endf` skips the slow part (NJOY processing of ~120 evaluations). `htfbr-data endf --only W Al-27` processes a subset.

## Sources

The registry lives in `config/sources.yaml` (tier A evaluated/primary, B handbook, C single paper or computed).

| Source | What it gives | Ingester |
| --- | --- | --- |
| IAEA LiveChart of Nuclides (API) | Abundances, half-lives, decay modes, masses for ~3,400 nuclides | `ingest/livechart.py` |
| ENDF/B-VIII.0, NNDC | Evaluated neutron cross sections, reconstructed and broadened with NJOY2016, averaged over standard spectra | `ingest/endf_xs.py` |
| NIST-JANAF 4th ed. | Cp, S, H, formation enthalpy and Gibbs energy, 0-6000 K | `ingest/janaf.py` |
| CALPHAD databases (SGTE unary, COST 507, OpenCalphad, pycalphad and Thermochimica collections) | Phase equilibria: assessed systems, Gibbs energies of solid and liquid phases; SGTE element melting points | `ingest/calphad.py` |
| Handbooks and papers | Thermophysical and mechanical properties | `data/manual/*.csv` -> `ingest/manual.py` |

Blocked or not yet implemented sources are listed with their reason in `config/sources.yaml` (`htfbr-data status` prints them).

## CALPHAD databases

`htfbr-data calphad` fetches each database listed under `calphad_files` in `config/targets.yaml` (raw files pinned to a repository commit, cached as artifacts) and loads it with pycalphad. It records:

- which element systems are *assessed*: a condensed-phase parameter spans their elements;
- whether the liquid is assessed;
- repeated parameters. pycalphad sums repeats, which silently doubles a Gibbs energy, so repeats are removed from TDB files and reported for DAT files. The SGTE copy had three; one doubled tin's rhombohedral phase energy and hid tin's melting point.

The needed systems (`calphad_systems_needed`) are compared with what is loaded in the generated [CALPHAD coverage](calphad-coverage.md) page. Actinide systems (U–Pu–Zr, U–Fe, U–W, U–Al, Ca–U, Pb–U) are the main gap: they need TDBDB, NIMS CPDDB, NIST, ORNL MSTDB-TC or paper supplements, all currently unreachable or not yet entered.

Element melting points from SGTE are stored in `property` (source `sgte_unary`, method `calculated`) and used by the claims check where JANAF has no data.

## Design rules

- Raw files are cached under `data/raw/<source_id>/` and never edited. Re-fetches with new content create new artifacts.
- Large libraries are read member-by-member with HTTP range requests (`fetch.RemoteZip`).
- Manual entries need a registered `source_id`, a `locator` (page, table, equation or DOI) and a unit pint understands; rows that fail are rejected, not repaired.
- Derived values (spectrum averages, vapour pressures, natural-element cross sections) record the method used, and the weighting functions are defined exactly in the `weighting` table.
- Gaps are reported, never filled with estimates.

## Layout

```
config/      sources.yaml, targets.yaml (what to ingest), quantities.yaml, claims.yaml (doc figures to check)
htfbr_data/  schema.sql, db, fetch (cache + range zip), registry, chem, thermo, checks, cli, ingest/*
data/        htfbr.sqlite, raw/ (cached downloads), manual/ (hand-entered CSVs)
reports/     claims_check.md/.csv, run logs
tests/       unit tests with small real fixtures
```

## Known limitations

- Spectrum averages use standard weightings (2200 m/s, Maxwellian, 1/E resonance integral, U-235 Watt spectrum). Averages over an actual HT-FBR core spectrum need an OpenMC transport calculation; the `weighting` table is ready to take those spectra.
- Infinite-dilution averages: no self-shielding.
- JANAF lacks U, Th, Y and Sn species and HfO2. SGTE now supplies their element melting points; compound formation energies still need Konings 2014 or NEA-TDB (registered, manual).
- CALPHAD files from software repositories are tier C until each is traced to its published assessment; open repositories have almost no actinide systems.
- Vapour pressures are for the monomer only and only below the element's tabulated boiling point.

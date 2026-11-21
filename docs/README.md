# Documentation map

The project explores many reactor designs built from many materials. The documentation is organised so you can enter from either side (a design, a material, or a question) and follow links to everything related.

```
          framework/                 how we classify and screen
          taxonomy, screening
                 |
 project/ ---> designs/  <------->  materials/  <---- data/ (database)
 brief,        one page per         one page per
 targets       candidate design     material
                 ^      \            ^
                 |       \           |
            studies/   decisions/  open-questions.md
            analyses   why we chose  what we don't know yet
```

## Where things live

| Folder | Contains | Page type |
| --- | --- | --- |
| [project/](project/) | [Brief](project/brief.md) (mission, targets, premises, work packages), [state of the art and efficiency limits](project/state-of-the-art.md), [roadmap](project/roadmap.md) (phases, gates, next steps) | Narrative, changes rarely |
| [framework/](framework/) | [Design taxonomy](framework/taxonomy.md) (10 axes, designation codes, exclusion rules), [materials selection method](framework/materials-selection.md) (candidate generation across all material classes, chemistry rules), [materials screening](framework/materials-screening.md) (gates, scoring, stacks) | Method, changes rarely |
| [designs/](designs/README.md) | One page per candidate design, indexed by ID, status and key parameters | Record, one per design |
| [materials/](materials/README.md) | One page per material: role, properties (generated from the database where possible), compatibility, designs using it | Record, one per material |
| [studies/](studies/README.md) | Cross-cutting analyses that compare options or explore a theme (industrial heat, ~2,000 °C liquid fuel, aluminium coolant) | Narrative |
| [decisions/](decisions/README.md) | Decision log: what was decided, why, and what it rules out | One file per decision |
| [open-questions.md](open-questions.md) | Numbered open questions and go/no-go tests, linked to the designs and materials they block | Register |
| [data/](data/database.md) | How the property database works, its sources, and the latest check of doc figures against it | Reference |
| [glossary.md](glossary.md) | Terms and abbreviations | Reference |

## Conventions

- **After every study, update the "Most promising design options" summary in the [top-level README](../README.md#most-promising-design-options)** (ranking, numbers, parked list, cross-cutting findings) and its `Updated:` date. `tests/test_docs.py` fails if that date is older than the newest study.

- **IDs.** Designs: `B1`–`B6` (seed branches), `X1`–`X3` (liquid fuel at ~2,000 °C), `A1`–`A3` (aluminium-cooled); new families get a new letter. Decisions: `D-0001`. Questions: `Q-001`. Materials: lowercase slugs (`aluminium`, `zirconium-diboride`).
- **Front matter.** Every design and material page starts with a YAML header (ID, status, key parameters, links). `htfbr-data docs` builds the index tables from it, so add a page and run the command; never edit an index table by hand.
- **Status values.** Designs: `seed` (named only), `exploring` (being analysed), `analysed` (feasibility assessed), `parked`, `rejected`. Materials: `candidate`, `shortlisted`, `excluded`.
- **Numbers.** A figure is either from the database (tagged with its source in generated blocks), from a cited document, or marked *(approx.)*. Unsourced values are being replaced; [data/claims-check.md](data/claims-check.md) shows which have been verified.
- **Generated blocks.** Text between `<!-- BEGIN GENERATED ... -->` and `<!-- END GENERATED -->` is rewritten by `htfbr-data docs`. Edit outside those markers.
- **Figures.** SVGs in [assets/figures/](assets/figures/) are rendered from editable sources in `tools/figures/src/` (`cd tools/figures && npm install && npm run render`). Edit the source, never the SVG; data charts keep their values in the source with a note on where each comes from.
- **Templates.** [designs/_template.md](designs/_template.md), [materials/_template.md](materials/_template.md), [decisions/_template.md](decisions/_template.md).

## How to add things

| To add | Do |
| --- | --- |
| A design | Copy `designs/_template.md` to `designs/<ID>.md`, fill the header, run `htfbr-data docs` |
| A material | Copy `materials/_template.md` to `materials/<slug>.md`, set `db_key` so database facts can be generated, run `htfbr-data docs` |
| A decision | Copy `decisions/_template.md` to `decisions/D-<next>.md`, add a row to the log |
| An open question | Add a row to `open-questions.md` with the next `Q-` number and links |
| A study | Add `studies/<slug>.md`, list it in `studies/README.md`, link it from the designs and materials it informs |

# Working in this repository

- The repository is the source of truth for the HT-FBR study; docs live in `docs/` (map: `docs/README.md`).
- After every study (or any result that changes the picture), update the **"Most promising design options"** section of the top-level `README.md`: ranking, key numbers, parked list, cross-cutting findings, and the `Updated:` date. `tests/test_docs.py` checks the date against the newest study in `docs/studies/README.md`.
- Regenerate indexes with `python -m htfbr_data.cli docs`, then run `python -m pytest` before committing.
- Label numbers *(calc)*, *(db)* or *(approx.)* as the docs do.

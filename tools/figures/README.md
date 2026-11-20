# Figures

Editable sources for the SVG figures in `docs/assets/figures/`. Each `src/<name>.jsx` default-exports a
component that returns an `<svg>`; `render.mjs` turns it into a standalone light-theme SVG with the same name.

```bash
npm install          # once: esbuild, react, react-dom (pinned)
npm run render       # all figures
node render.mjs a2-core-geometry   # one figure
```

Conventions (shared with the diagrams first drawn in the Claude Doc):

- Colours are tokens `var(--cds-...)`, mapped to fixed colours in `PALETTE` in `render.mjs`.
- Data charts wrap the drawing in `<claude.Visualize sources={{name: {kind: 'data', data: [...]}}}>`; values live
  in the source. Say where each value comes from (database, reference, or approximate) in a comment and on the chart.
- Every SVG must have a source and be used by a doc page; `python -m pytest` checks this.

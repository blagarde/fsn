// Render every src/<name>.jsx (a default-exported component returning an <svg>) to
// ../../docs/assets/figures/<name>.svg as a standalone light-theme SVG.
//
// Sources use the same conventions as the diagrams first drawn in the Claude Doc:
// colour tokens `var(--cds-...)` (mapped to PALETTE below) and, for data charts,
// <claude.Visualize sources={{name: {kind:'data', data:[...]}}}>{({name, datum}) => <svg/>}</claude.Visualize>.
import { readdirSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join, dirname, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { transformSync } from "esbuild";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

const HERE = dirname(fileURLToPath(import.meta.url));
const SRC = join(HERE, "src");
const OUT = join(HERE, "..", "..", "docs", "assets", "figures");

const PALETTE = {
  "--cds-text-primary": "#1f1f1f",
  "--cds-text-secondary": "#5c5c5c",
  "--cds-chart-muted": "#b5b2a7",
  "--cds-chart-grid": "#e4e4e4",
  "--cds-chart-axis": "#9b9b9b",
  "--cds-chart-reference": "#8a8a8a",
  "--cds-chart-reference-tint": "#efeee9",
  "--cds-chart-categorical-1": "#2a6fd4",
};

// Shim for the Claude Docs chart wrapper: hand each declared source's rows to the child function.
const claude = {
  Visualize: ({ sources, children }) => {
    const args = { datum: () => ({}) };
    for (const [name, src] of Object.entries(sources)) args[name] = src.data;
    return children(args);
  },
};

function load(file) {
  const code = readFileSync(file, "utf8");
  const { code: js } = transformSync(code, { loader: "jsx", jsx: "transform", format: "cjs" });
  const module = { exports: {} };
  new Function("React", "claude", "module", "exports", js)(React, claude, module, module.exports);
  return module.exports.default;
}

function finish(markup) {
  let svg = markup.replace(/var\((--cds-[a-z0-9-]+)\)/g, (m, v) => {
    if (!(v in PALETTE)) throw new Error(`unmapped colour token ${v}`);
    return PALETTE[v];
  });
  // standalone file: namespace, font, white background so it reads on GitHub's dark theme too
  svg = svg.replace(/^<svg /, '<svg xmlns="http://www.w3.org/2000/svg" font-family="Inter, Helvetica, Arial, sans-serif" ');
  svg = svg.replace(/^(<svg[^>]*>)/, '$1<rect width="100%" height="100%" fill="#ffffff"/>');
  // drop editor-only attributes
  svg = svg.replace(/ data-claude-[a-z-]+="[^"]*"/g, "");
  return '<?xml version="1.0" encoding="UTF-8"?>\n' + svg + "\n";
}

mkdirSync(OUT, { recursive: true });
const only = process.argv.slice(2);
for (const f of readdirSync(SRC).filter((f) => f.endsWith(".jsx")).sort()) {
  const name = basename(f, ".jsx");
  if (only.length && !only.includes(name)) continue;
  const svg = finish(renderToStaticMarkup(React.createElement(load(join(SRC, f)))));
  writeFileSync(join(OUT, `${name}.svg`), svg);
  console.log(`rendered ${name}.svg (${svg.length} bytes)`);
}

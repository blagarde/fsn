# D-0005: Project documentation lives in this repository

- **Date:** 2026-11-20
- **Status:** accepted
- **Affects:** [docs/README.md](../README.md)

## Context

Designs, materials and studies were in a single Claude Doc. Many designs and materials are expected, and figures must trace to the property database.

## Decision

Markdown in this repository is the source of truth: one page per design and material, indexes generated from page headers, material facts generated from the database. The Claude Doc becomes an overview linking here.

## Consequences

Doc changes go through git on main. Narrative discussion can still happen in the Claude Doc, but conclusions are copied here.

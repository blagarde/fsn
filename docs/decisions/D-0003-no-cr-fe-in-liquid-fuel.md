# D-0003: No Cr or Fe in liquid U-Pu fuel by default

- **Date:** 2026-11-19
- **Status:** accepted
- **Affects:** [liquid U–Pu metal](../materials/uranium-plutonium-metal.md), [X1–X3](../designs/README.md), [A2](../designs/A2.md)

## Context

Cr or Fe additions lower the freezing point of U–Pu fuel (U–Cr ~860 °C, U–Fe ~725 °C vs ~1,130 °C) but dilute heavy metal, soften the spectrum somewhat and add activation (Fe-59, Mn-54, Cr-51). At ~2,000 °C pure U–Pu is already liquid.

## Decision

Default fuel is unalloyed U–Pu; additions are a screening trade-off for shutdown freeze margin only.

## Consequences

Guard heating must keep the plant above ~1,100 °C. Revisit if freeze/drain analysis ([Q-025](../open-questions.md)) shows the margin is unworkable.

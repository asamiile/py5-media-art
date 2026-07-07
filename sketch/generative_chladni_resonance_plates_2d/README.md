# generative_chladni_resonance_plates_2d

**Date**: 2026-07-07
**Type**: Animation (10-30s @ 60fps)

## Concept
A simulation of Chladni patterns, where thousands of fine particles on a vibrating 2D plate settle into the nodal lines of complex acoustic resonance frequencies. The frequency slowly shifts, causing the particles to chaotically bounce and reorganize into new, beautiful geometric mandalas.

## Techniques
Uses a particle system (hundreds of thousands of points). The plate's vibration amplitude at any `(x, y)` is calculated using standing wave equations `sin(n*x)*sin(m*y) ± sin(m*x)*sin(n*y)`. Particles are pushed away from high-amplitude areas (antinodes) and settle into low-amplitude areas (nodes) via a magnitude-dependent random walk. The parameters `n` and `m` morph continuously over time. Rendered via fast numpy points drawing.

## Palette
Elegant monochrome sand. Golden/sand colored fine particles scattered across a deep, rich mahogany or matte black background.

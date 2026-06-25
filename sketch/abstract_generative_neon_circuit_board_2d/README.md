# abstract_generative_neon_circuit_board_2d

An animated 15s sequence of a generative neon circuit board in 2D.

## Concept

A labyrinth of neon circuit board traces generating dynamically across the canvas. It resembles a cyberpunk city map or a dense microprocessor layout being built in real-time.

## Technique

A grid-based procedural generation system where lines "grow" from seeds, moving orthogonally and leaving bright glowing trails. When they hit other trails or reach the bounds, they stop and create a bright node (via). Occasionally, new paths branch off to keep the density increasing, creating a dense glowing circuitry over time.

## Palette

- Background: Void dark blue (0, 0, 5)
- Circuit Traces: Cyberpunk cyan, blue, with occasional magenta accents
- Nodes (Vias): High-intensity pure white

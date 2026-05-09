# Bioluminescent Mycelial Network

A 3D agent-based simulation of organic growth and self-organization in the cosmic void.

## Concept

This artwork explores the emergence of complex networks through simple local rules, inspired by the growth patterns of *Physarum polycephalum* (slime mold) and fungal mycelia. In the vast silence of the universe, light self-organizes into silken threads that branch, merge, and pulse with a hidden biological intelligence.

## Technical Details

- **Simulation**: 200,000 autonomous agents navigating a 128x128x128 3D pheromone field.
- **Algorithm**: Implement a 3D extension of the Physarum transport network model. Agents sense field gradients, deposit trails, and follow a steer-to-high-density logic.
- **Processing**: Vectorized agent updates using NumPy and volumetric field manipulation (diffusion/decay) via Scipy's Gaussian filters.
- **Rendering**: Multi-pass additive point rendering in P3D with a bioluminescent palette (Cyan, Amethyst, and Electric White).
- **Environment**: 4K/60fps animation with a shimmering background starfield.

## Aesthetics

The visual narrative follows the transition from a chaotic cloud of initial agents into a structured, shimmering web of light. The "Bioluminescent Cyan" trails represent the exploring frontiers, while the "Royal Amethyst" and "White" nodes mark the established pathways of the cosmic network.

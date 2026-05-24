# lbm_karman_vortex_street

**Date**: 2026-05-22
**Format**: 15s 4K/60fps MP4
**Algorithm/Technique**: Vectorized 2D Lattice Boltzmann Method (D2Q9) simulation. Visualizes the Von Kármán vortex street in a turbulent fluid flow.

## Concept

The mesmerizing, repeating pattern of swirling vortices created by a fluid as it is forced around an obstacle, visualizing the sheer mathematical complexity and hidden beauty of turbulent flow.

## Implementation Notes

- Implements a pure-NumPy D2Q9 Lattice Boltzmann solver computing 9 density functions across over 120,000 cells.
- Utilizes half-way bounce-back boundary conditions for the cylindrical obstacle and zero-gradient outflow.
- Dynamically computes local vorticity ($\nabla \times \vec{u}$) to reveal alternating vortex shedding from the cylinder.
- Renders the flow field using a stunning diverging colormap: clockwise eddies shed in crimson/orange, while counter-clockwise eddies shed in teal/cyan, contrasting against the deep abyss blue of the laminar flow.

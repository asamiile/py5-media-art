# fluid_mosaic

A generative artwork simulating the biological "fluid mosaic" model of cell membranes.

## Concept
The piece visualizes the dynamic, ever-shifting nature of biological membranes. It portrays a microscopic landscape where large protein complexes drift through a fluid sea of phospholipids, illustrating the fundamental organizational principle of life at the molecular scale.

## Technique
- **Dual-Scale Particle Simulation**: Simulates the movement of hundreds of small "lipids" and several large "protein" agents.
- **Noise-Driven Fluidity**: OpenSimplex noise generates an evolving velocity field that drives the organic, swirling motion of the membrane components.
- **Accumulated Motion Trails**: The simulation runs for several hundred steps, building up semi-transparent trails that create a shimmering, textured background.
- **Molecular Detail Layer**: A final crisp layer adds highlights, internal protein subunits, and varied teal/seafoam lipid shades for a rich, biological feel.
- **Extracellular Matrix**: Thin, wispy Bezier curves in the background provide depth and context to the cellular environment.

## Metadata
- **Date**: 2026-05-02
- **Theme**: molecular biology, cell membrane, fluidity, life
- **Technique**: fluid simulation, particle systems, noise-based velocity fields, multi-layer rendering

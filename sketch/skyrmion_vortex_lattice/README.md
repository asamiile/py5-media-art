# skyrmion_vortex_lattice

A majestic 3D visualization of a Skyrmion lattice—a topological structure found in magnetic materials where spins wrap around a core in a stable, knot-like configuration.

## Concept
Skyrmions are quasiparticles with a non-zero topological charge. This piece explores the collective dynamics of a lattice of these magnetic vortices, visualizing the silken flow of "spins" as they twist and warp around stable cores.

## Technique
- **Simulation**: 150,000 "spin tracer" particles in 3D. A lattice of 9 skyrmion cores is defined. Particles are advected by the local "spin torque" field of the nearest cores.
- **Dynamics**: The skyrmion cores oscillate and drift slowly, causing the surrounding particle "vortices" to warp and reconnect in complex, silken patterns.
- **Rendering**: Multi-pass additive point rendering. Particle brightness and color are determined by the local field strength (vortex intensity).
- **Palette**: "Emerald Glow / Burnished Gold / Deep Ultraviolet" against a star-dusted obsidian void.

## Format
- **Animation**: 10 seconds @ 60fps
- **Resolution**: 3840x2160 (4K)
- **Engine**: py5 (Python implementation of Processing)

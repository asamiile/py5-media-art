# algorithmic_crystal_growth

## Metadata
- **Date**: 2026-05-23
- **Theme**: A dynamic, bismuth-like crystal lattice that aggressively grows and branches out in real-time 3D spa
- **Technique**: Unknown
- **Logic Lab Reference**: 

## Concept
A dynamic, bismuth-like crystal lattice that aggressively grows and branches out in real-time 3D space.

- **Date**: 2026-05-23
- **Theme**: Algorithmic botany, DLA (Diffusion-Limited Aggregation), crystallography, bismuth.
- **Technique**: Uses a 3D NumPy grid (30x30x30) to track crystal nodes. The growth algorithm starts with a single central seed. Every frame, it randomly selects active nodes (biased towards newer nodes via a Beta distribution to encourage branching rather than a solid blob) and spawns neighbors in the 6 cardinal directions. Once a node is formed, it records its "generation" (age). The sketch renders each node using `py5.box` with size and neon HSB coloring determined by its generation. The result is a rapidly branching, fractal-like structure similar to bismuth crystals. Rendered in P3D with directional lighting. 15s 60fps MP4.
- **Description**: In the center of a dark void, a tiny glowing cube appears. Suddenly, it rapidly branches outward in straight lines, spawning thousands of cubic "crystals" that aggressively build a complex, jagged, alien structure in 3D space. As the giant crystalline lattice rotates, its nested layers shimmer in a hypnotic rainbow gradient, highly reminiscent of metallic bismuth crystals.

## Technical Details
- **Renderer**: P3D
- **Simulation**: Unknown
- **Visuals**: Unknown
- **Animation**: Contains animation details

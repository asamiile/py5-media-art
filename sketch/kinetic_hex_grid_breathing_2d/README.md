# kinetic_hex_grid_breathing_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
A precise, interlocking honeycomb grid of glowing geometric shapes. The sketch juxtaposes rigid mathematical structure with organic, flowing movement, creating the illusion of a living, breathing mechanical surface or a futuristic interface.

## Techniques
- **Hexagonal Tiling**: A dense grid of hexagons is mathematically calculated to cover the canvas perfectly (using standard $\sqrt{3}R$ and $1.5R$ offsets).
- **Nested Geometries**: Each cell contains three concentric hexagons. Instead of moving uniformly, these nested shapes rotate in opposing directions and at different speeds, creating complex interlocking "gears" within every cell.
- **Noise Mapping**: Two distinct 3D OpenSimplex noise fields (`py5.os_noise`) control the grid. One determines the base color (cyan, magenta, yellow) creating large, slowly shifting "islands" of color. The other modulates the local scale and rotation of each hexagon.
- **Breathing Effect**: As the noise Z-axis (time) advances, waves of scaling and rotation ripple across the canvas, making the rigid grid appear to breathe.

## Palette
Cyberpunk neon cyan, magenta, and yellow on a dark background.

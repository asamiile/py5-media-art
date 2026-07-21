# kinetic_wireframe_terrain_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
A love letter to the Synthwave and Outrun aesthetics of the 1980s retro-future. The animation simulates a high-speed flight over an undulating, neon wireframe landscape towards a glowing digital sun on the horizon.

## Techniques
- **3D to 2D Projection**: Instead of relying on a 3D renderer, the script manually calculates 3D coordinates `(x, y, z)` and projects them into 2D orthographic space using trigonometric functions, ensuring perfect crisp lines.
- **Noise-Driven Flight**: The height (`z`) of each point on the grid is determined by an OpenSimplex noise field. To create the illusion of flying forward, the Y-offset of the noise sampling is shifted over time.
- **Topographic Coloring**: The stroke color of the terrain maps directly to its elevation, fading seamlessly from bright neon pink at the peaks to deep cyan in the valleys, while fading to black in the distance.
- **Glowing Sun**: The background features a classic layered Synthwave sun, created by drawing multiple transparent, expanding circles with `ADD` blend mode to simulate bloom.

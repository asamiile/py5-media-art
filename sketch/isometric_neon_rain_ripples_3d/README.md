# isometric_neon_rain_ripples_3d

An animated 15s sequence of neon magenta and cyan raindrops falling onto a metallic grid and creating glowing circular ripples.

## Theme
A 3D isometric simulation of a minimalist rainstorm.

## Technique
Orthographic 3D projection using `py5.ortho()`. A flat plane composed of a dense grid. Raindrops are particles falling from the sky. When they hit the grid, they spawn expanding circular ripples. The ripples intersect and create interference patterns, mapped to bright cyan and magenta colors against a dark background with additive blending.

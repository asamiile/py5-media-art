# Neon Cyberpunk Infinity City 3D

## Concept
A cinematic flyover of an infinite, glowing futuristic city. The camera glides steadily forward over a shifting, procedural skyscraper range composed entirely of neon wireframes and translucent data-surfaces.

## Technique
* Procedural grid generation with `py5.box()` mapped to a rolling 2D `py5.os_noise()` height map.
* Modulo coordinate system to create the illusion of an infinite scrolling grid.
* Additive blending with deep color hues mapped by building heights.
* Directional and ambient lighting to simulate neon-lit cyberpunk streets.

## Palette
* Cyberpunk Neon (Cyan, Magenta, Violet, Deep Blue)
* Additive blending (`py5.ADD`)

## Specifications
- Resolution: 3840x2160
- Frame Rate: 60 FPS
- Duration: 10s (600 Frames)
- Architecture: Python `py5` with heavily optimized grid drawing

## Notes
The grid size is optimized to 40x40 to maintain realtime rendering speeds while delivering high geometric density. Taller "mega-buildings" are probabilistically spawned and tinted a complementary contrast color.

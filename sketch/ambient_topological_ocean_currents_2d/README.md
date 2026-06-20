# ambient_topological_ocean_currents_2d

An abstract, calming representation of ocean currents moving across a topological map.

## Details

- **Type**: 2D animation
- **Length**: 10 seconds (60fps)

## Technique

15,000 faint blue/teal particles are drawn on a 2D canvas, driven by an evolving vector flow field using multi-scale Perlin noise. The particles leave long trails with very slow alpha decay, creating silky, continuous lines that wrap around the screen. Additive blending is used to make overlapping currents glow brightly.

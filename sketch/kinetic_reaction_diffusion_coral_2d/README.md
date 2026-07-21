# kinetic_reaction_diffusion_coral_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
A glowing, organic cellular simulation that grows and divides into intricate brain-coral and maze-like Turing patterns. The shapes start as small seeds and organically self-replicate, growing to fill the canvas with alien, biological textures.

## Techniques
- **Reaction-Diffusion**: Simulates the continuous Gray-Scott reaction-diffusion mathematical model across a 2D grid, representing two imaginary chemicals interacting and diffusing.
- **Vectorized Laplacian**: Uses fast NumPy array slicing instead of slow nested loops to compute the 3x3 discrete Laplacian operator, allowing thousands of grid cells to be updated at 60fps.
- **Dynamic Parameters**: The feed ($F$) and kill ($k$) rates modulate slightly over time and space. The spatial variance creates different pattern types (spots vs. stripes) across the canvas, and the temporal variance causes the "coral" to breathe and morph as it grows.

## Palette
A highly toxic, acidic glowing neon yellow and green palette used for the structures, sitting on a deep, dark violet void background.

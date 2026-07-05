# kinetic_strange_attractor_particle_swarm_2d

**Date**: 2026-07-05
**Type**: Animation (10-30s @ 60fps)

## Concept
A visual exploration of chaotic strange attractors mapped into a 2D space. 150,000 tiny glowing particles trace the complex chaotic orbits, sweeping out detailed, gossamer-like folded structures that evolve as the attractor parameters slowly drift over time.

## Techniques
Initializes 150,000 particles at random coordinates. Every frame, applies a parameterized Clifford strange attractor equation to update each particle's position. The parameters of the equation (a, b, c, d) slowly interpolate using a smoothstep function, causing the entire swarm to smoothly mutate from one attractor shape into another. Rendered with additive blending using py5.POINTS.

## Palette
Iridescent bioluminescence. Deep void black background, with glowing cyan, electric magenta, and warm gold particles.

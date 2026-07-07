# kinetic_particle_physics_gravity_wells_2d

**Date**: 2026-07-07
**Type**: Animation (10-30s @ 60fps)

## Concept
A physics simulation of thousands of particles caught in the gravitational pull of multiple orbiting gravity wells. The wells dance around the center in complex Lissajous curves, pulling the particles into intricate, stylized orbital patterns that resemble a cosmic galaxy or planetary system.

## Techniques
The simulation relies on a custom $O(N \times M)$ physics engine built with NumPy vectorization, where $N=30,000$ particles interact with $M=4$ gravity wells plus one supermassive central well. Newton's law of universal gravitation is simulated with a softening parameter to prevent particles from slingshotting to infinity. As particles move, they are drawn with additive blending against a fading background to create long, glowing orbital trails.

## Palette
Cosmic gold. A deep, infinite black background with particles glowing in bright golds, ambers, and stark whites.

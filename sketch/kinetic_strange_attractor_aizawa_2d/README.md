# kinetic_strange_attractor_aizawa_2d

**Date**: 2026-07-07
**Type**: Animation (10-30s @ 60fps)

## Concept
A generative visualization of the Aizawa strange attractor. We simulate thousands of particles tracing the paths of the chaotic Aizawa equations. As they move, they draw glowing trails that slowly build up a beautiful, sphere-like complex chaotic structure in 2D projection. The attractor slowly rotates in 3D space before being projected to 2D.

## Techniques
The Aizawa attractor equations are solved using simple Euler integration for 50,000 points concurrently using NumPy. 
The 3D points are then rotated around the Y and X axes and projected orthogonally to 2D.
To keep it fast, we do the math in NumPy, project, and draw them as tiny points with additive blending, creating a dense glowing volumetric cloud.

## Palette
Neon plasma. A deep amethyst background with the attractor particles glowing in cyan, magenta, and gold. Color is divided into groups of particles to give a layered, volumetric structure.

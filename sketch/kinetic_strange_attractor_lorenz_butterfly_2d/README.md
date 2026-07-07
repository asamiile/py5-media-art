# kinetic_strange_attractor_lorenz_butterfly_2d

**Date**: 2026-07-07
**Type**: Animation (10-30s @ 60fps)

## Concept
A 3D chaotic strange attractor (like the Lorenz attractor) rendered as a continuously growing, glowing thread that slowly rotates in space. As the thread grows, the older segments fade away, creating a beautiful "butterfly" wing effect tracing the chaotic orbits.

## Techniques
Uses the Lorenz equations `dx/dt = sigma*(y - x)`, `dy/dt = x*(rho - z) - y`, `dz/dt = x*y - beta*z`. The system is integrated over time to generate points in 3D space. The points are projected and rotated. A `py5.begin_shape()` is used to draw a fading trail of the last 150 positions for 150 different particles.

## Palette
Neon bioluminescence. Deep oceanic blue background with the attractor glowing in intense cyan, shifting to bright magenta at the extremes.

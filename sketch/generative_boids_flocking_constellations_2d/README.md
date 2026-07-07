# generative_boids_flocking_constellations_2d

**Date**: 2026-07-07
**Type**: Animation (10-30s @ 60fps)

## Concept
A simulation of generative "constellations" forming in real-time. Thousands of glowing particles flow through a chaotic noise field, mimicking the fluid movement of flocking birds or neural pathways. Whenever two particles get close enough, a thin glowing line connects them, creating a dynamic, shifting neural network or constellation pattern.

## Techniques
Particles update their velocities based on a Perlin noise vector field (flow field). For the connections, NumPy vectorization (`scipy.spatial.distance` equivalent via broadcasting) efficiently calculates all pairwise distances each frame. Lines are drawn with distance-based alpha blending between any pair of particles within a certain radius.

## Palette
Deep space neural network. Deep navy/black background with particles glowing in soft ethereal blues and purples. The connecting lines are bright white and semi-transparent, creating an intricate web of light.

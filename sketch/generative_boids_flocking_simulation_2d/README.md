# generative_boids_flocking_simulation_2d

## Theme
A simulation of avian murmuration, where hundreds of digital entities flock and weave across the canvas, guided by shifting invisible currents.

## Technique
Uses a modified boids steering behavior algorithm optimized for Python execution speed. Rather than O(N^2) pairwise distance checks for alignment and cohesion, the boids are steered by a globally continuous 3D OpenSimplex noise field that mimics macroscopic group flow. The boids are drawn as oriented triangles that leave semi-transparent trails as they move.

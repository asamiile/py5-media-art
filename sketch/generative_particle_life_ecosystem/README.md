# generative_particle_life_ecosystem

![Preview](generative_particle_life_ecosystem_p1.png)

A simulation of "Particle Life" or continuous artificial life, built with Py5 and NumPy vectorization. By defining a small set of simple interaction rules between 4 different "species" (colors) of particles—where forces of attraction and repulsion continuously shift—incredibly complex, organic, emergent behaviors arise.

The behavior is governed by a 4x4 interaction matrix. To make the ecosystem kinetic and constantly evolving, the values in the interaction matrix slowly oscillate over time using Perlin noise. This causes the particle swarms to continuously transition between chaotic motion, structured cell-like membranes, and worm-like formations. Rendered in 4K using additive blending and simulated motion blur.

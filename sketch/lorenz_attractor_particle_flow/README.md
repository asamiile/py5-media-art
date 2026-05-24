# lorenz_attractor_particle_flow

A massive fluid-like particle flow charting the chaotic paths of the 3D Lorenz Strange Attractor.

- **Date**: 2026-05-23
- **Theme**: Chaos theory, strange attractors, meteorology, fluid dynamics.
- **Technique**: 200,000 independent particles are initialized in a tight cluster near the origin and iteratively integrated through the classical Lorenz equations using a high-speed vectorized NumPy Euler solver. Instead of drawing static lines, the particles dynamically flow through the attractor's phase space, leaving decaying, semi-transparent light trails. The 3D coordinates are rotated with a virtual camera and projected directly into the `py5.np_pixels` buffer using additive blending. Colored based on their vertical (Z) position, creating a glowing gradient from Deep Purple to Hot Pink to Bright Orange. 15s 60fps MP4.
- **Description**: A tight knot of glowing plasma explodes outward, rapidly tracing the iconic butterfly wings of the Lorenz attractor. The particles flow like a torrential, glowing fluid, endlessly looping and crossing between the two chaotic basins. The camera slowly orbits the structure, revealing the infinitely thin, fractal layers that make up this beautiful mathematical anomaly.

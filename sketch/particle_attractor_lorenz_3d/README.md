# particle_attractor_lorenz_3d

A massive particle swarm visualizing the chaotic Lorenz attractor in 3D space.

- **Date**: 2026-05-23
- **Theme**: Chaos theory, strange attractors, vector fields, particle physics.
- **Technique**: Evaluates the Lorenz system equations ($\sigma=10, \rho=28, \beta=8/3$) simultaneously for 30,000 independent particles using highly optimized vectorized NumPy arrays. Each frame, the local vector field determines the velocity of every particle, driving them to orbit the two strange attractor "wings." The rendering uses P3D with `py5.POINTS` and additive blending, combined with a semi-transparent black rectangle over the screen to produce beautiful motion-blurred trails. The color of each particle is dynamically tied to its instantaneous speed and the global time. 15s 60fps MP4.
- **Description**: 30,000 brightly colored neon sparks swirl through a black void, caught in the invisible currents of a mathematical storm. They trace out the famous "butterfly wings" of the Lorenz strange attractor, looping endlessly from one side to the other. Thanks to additive blending, dense clusters of particles glow with intense, blinding light, while fast-moving outliers leave sweeping, wispy rainbow trails behind them as the entire shape slowly rotates.

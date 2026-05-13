# wigner_crystal_melting

- **Theme**: Quantum phase transition, Wigner crystallization, melting, Coulomb repulsion, collective dynamics.
- **Technique**: 2D particle simulation with $1/r$ repulsive forces and a harmonic trap. Brownian dynamics with time-varying temperature. Vectorized NumPy physics.
- **Palette**: "Electric Ice / Neon Amethyst / Deep Indigo / Solar White".
- **Description**: A rigid, shimmering hexagonal lattice of blue-white stars that slowly vibrates, develops defects, and eventually melts into a chaotic, swirling sea of violet and cyan light as the quantum temperature rises.

## Technical Details

- **Simulation**: 1,200 particles with $1/r^2$ Coulomb repulsion and a central harmonic trap.
- **Dynamics**: Velocity-Verlet integration with damping and stochastic noise (Brownian term).
- **Transition**: The noise magnitude (temperature) increases linearly over 20 seconds, triggering the melting of the Wigner crystal.
- **Rendering**: Multi-pass additive blending with glow halos.
- **Output**: 4K/60fps MP4.

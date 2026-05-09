# chromatic_planck_fluctuations

A mesmerizing visualization of the quantum vacuum at the Planck scale, where space-time is not a smooth manifold but a boiling, iridescent foam of virtual particles and fluctuating energy fields.

## Concept
At the smallest scales of reality, the vacuum is not empty. This piece explores the concept of "Quantum Foam" and virtual particles that are constantly born and annihilated, driven by the jittering energy of the Planck scale.

## Technique
- **Simulation**: 160,000 "virtual particles" are simulated in 3D. Each particle has a finite lifetime, after which it is "annihilated" and a new one is "born" at a stochastic location.
- **Foam Dynamics**: Particle movement is driven by a 3D noise-based field (using a precomputed 32x32x32 volume with high-order interpolation) representing the energy fluctuations of the vacuum.
- **Chromatics**: Particle colors and sizes are mapped to the local "energy density" (noise intensity), shifting from ultraviolet/deep indigo in low-energy regions to brilliant solar gold in high-fluctuation nodes.
- **Rendering**: Multi-pass additive point rendering with lifetime-based alpha modulation to create a ghostly, ephemeral aesthetic.

## Format
- **Animation**: 10 seconds @ 60fps
- **Resolution**: 3840x2160 (4K)
- **Engine**: py5 (Python implementation of Processing)

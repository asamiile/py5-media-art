# cosmic_filament_condensation

A majestic 3D visualization of the formation of the Cosmic Web, where baryonic matter condenses into intricate filaments and dense clusters under the influence of dark matter and primordial sound waves.

## Concept
The universe on its largest scales is not uniform, but a vast network of filaments and voids. This piece simulates the gravitational collapse of matter in the early universe, driven by primordial density perturbations and modulated by baryon acoustic oscillations (BAO).

## Technique
- **Simulation**: 200,000 particles in 3D space using vectorized NumPy for physical integration.
- **Clustering**: Particles are attracted to 12 dynamic "dark matter hubs" using a modified $1/r^{1.5}$ gravitational potential to encourage silken filament formation.
- **BAO Oscillation**: A global harmonic oscillation modulates the particle velocities, simulating the sound waves that rippled through the primordial plasma.
- **Rendering**: Multi-pass additive point rendering with density-based color mapping.
- **Palette**: Crystalline White (high density cores), Ionized Magenta (heated filaments), and Deep Cobalt (dark matter halos).

## Format
- **Animation**: 20 seconds @ 60fps
- **Resolution**: 3840x2160 (4K)
- **Engine**: py5 (Python implementation of Processing)

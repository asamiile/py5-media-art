# Axion Field Flux

A generative media art animation visualizing the hypothetical Axion dark matter field and its conversion into photons via the Primakoff effect.

## Concept

This work explores the spatial topology and phase oscillation of the Axion field—a leading candidate for dark matter. The simulation depicts a "Primakoff conversion" event where axions passing through a cosmic magnetic field transform into shimmering photons.

The axion flux is modeled as a massive, pulsing scalar field that self-organizes into ghostly, iridescent filaments and shells. Unlike directional particle streams, this field evolves according to its own internal phase, creating a shimmering, ethereal texture that represents the hidden energy structures of the universe.

## Technical Details

- **Simulation**: 3D high-density particle system (240,000 particles) using vectorized NumPy.
- **Physics**: 
    - Particles are sampled from a multi-harmonic 3D scalar field $\phi(x, t)$.
    - Visibility (alpha) is modulated by the local field phase $\sin(\phi + \omega t)$ and proximity to a central "flux string."
    - Implements a "conversion probability" mapping from dark-matter (ghostly indigo/cyan) to luminous photon (white-gold) states.
- **Rendering**: Multi-pass additive spectral rendering with a high-density background starfield (12,000 stars).
- **Format**: 15-second 60fps 4K animation (3840x2160).

## Visual Impression

A majestic, shimmering cloud of light that pulses with a deep, rhythmic frequency. A central core of high-intensity white-gold light is surrounded by expanding shells of electric indigo and cyan, set against the silent obsidian void.

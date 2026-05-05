# quantum_vorticity

A generative animation of superfluid turbulence, exploring the concept of quantized singularities and liquid-like phase resonance.

## Concept
The work visualizes "quantum vortices" as they interact and tangle in a zero-viscosity superfluid. 30,000 particles are advected along the velocity field of multiple rotating singularities, creating an intricate tapestry of shimmering filaments. This piece captures the rhythmic beauty of quantized phase-space under a star-dusted night sky.

## Technique
- **Point-Vortex Advection**: Particle motion driven by the superposition of 8 point-vortex velocity fields (Biot-Savart law in 2D).
- **High-Performance NumPy Advection**: Fully vectorized implementation allowing for 30,000 simultaneous particle simulations at high frame rates.
- **Spectral Spectral Mapping**: Filaments are color-coded in Electric Cyan, Royal Amethyst, and Gold using HSB mapping based on their local resonance.
- **Atmospheric Starfield**: A high-density starfield and darkest indigo background address the "beautiful night sky" request.

## Palette
- **Background**: Darkest Indigo (#020208)
- **Vortices**: Electric Cyan, Royal Amethyst, Gold
- **Stars**: Shimmering Silver

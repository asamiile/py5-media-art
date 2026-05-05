# spectral_filaments

A generative animation exploring the intricate, invisible magnetic architecture of the interstellar medium.

## Concept
The work visualizes "plasma loops" and "magnetic filaments" as they are shaped by massive, rotating dipole centers. 40,000 particles are advected along the field lines of multiple magnetic sources, creating a dense, shimmering web of silken threads. This piece captures the rhythmic resonance and structural complexity of the intergalactic medium.

## Technique
- **Magnetic Dipole Simulation**: Particle advection driven by the superposition of 4 rotating magnetic dipole fields ($B \propto r^{-2}$).
- **High-Performance Advection**: Fully vectorized NumPy implementation allowing for 40,000 simultaneous particle simulations at high frame rates.
- **HSB Spectral Variety**: Filaments are color-coded in Emerald, Gold, and Cobalt using HSB mapping, creating a rich, iridescent texture.
- **Deep Space Atmosphere**: A high-density starfield and darkest navy background address the "beautiful night sky" request.

## Palette
- **Background**: Deepest Navy (#020205)
- **Filaments**: Emerald Green, Molten Gold, Electric Cobalt
- **Stars**: Shimmering White/Silver

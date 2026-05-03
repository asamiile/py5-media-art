# spectral_mirage

A fleeting, prismatic illusion formed by light passing through a turbulent atmosphere of ice crystals.

## Concept

This artwork simulates the phenomenon of spectral dispersion—the separation of light into its constituent rainbow colors—as it refracts through fluctuations in atmospheric density. It evokes the feeling of a cold, shimmering mirage appearing in a midnight-navy sky, where light is fractured into delicate, crystalline filaments.

## Technique

- **Noise-Guided Ray Casting**: Thousands of light rays are traced through a 2D Perlin noise field representing "ice density" variations.
- **Spectral Dispersion**: Each ray is decomposed into multiple "wavelengths" (color channels), each with a unique refractive index. Shorter wavelengths (blue/violet) deflect more sharply than longer ones (gold/white), creating prismatic fringes.
- **Structured Beams**: Rays are grouped into "beams" rather than distributed uniformly, creating caustic-like clusters and more coherent geometric structures.
- **Additive Blending & Multi-Pass Rendering**: Each ray is drawn multiple times with varying thickness and alpha to create a soft, emissive glow.

## Visual Impression

A cold, shimmering veil of light that appears to shift and refract as if through glass; bright, thin filaments of color emerge from a dark abyss, pulsing with a sharp, crystalline brilliance.

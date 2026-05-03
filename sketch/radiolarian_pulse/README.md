# radiolarian_pulse

A pulsating, mineral life of a deep-sea microscopic skeleton, unfurling its intricate geometry in the dark abyss.

## Concept
This work explores the intersection of recursive geometry and marine biology. Using an icosphere as a base, the structure is subjected to spherical inversion—a mathematical transformation that flips the geometry inside out through a central point. The resulting "pulse" simulates the organic respiration of a radiolarian organism.

## Technique
- **Spherical Inversion**: $P' = P / |P|^2 \cdot R^2$, where $R$ is a dynamic radius pulsing over time.
- **Organic Noise**: 3D Perlin noise modulates the vertex positions before inversion, creating asymmetric, flowing structures.
- **Layered Rendering**: Multi-layered stroke rendering with SCREEN blending creates an ethereal, bioluminescent glow.
- **Bioluminescent Particles**: Floating gold accent particles with soft halos mimic drifting pollen or marine snow.

## Files
- `main.py`: The entry point and drawing logic.
- `preview.png`: A still image from the middle of the animation.
- `output.mp4`: The full 5-second animation.

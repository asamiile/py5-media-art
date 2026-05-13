# boid_flock

![Preview](preview.png)

## Metadata
- **Date**: 2026-04-25
- **Theme**: emergence, swarm intelligence, organic motion.
- **Technique**: Reynolds boid rules (separation/alignment/cohesion), vectorized numpy physics, heading-based HSV color, circular trail buffer.
- **Logic Lab Reference**: None

## Concept
300 boids forming emergent flocks; heading-angle coloring makes each flock a coherent color ribbon; 50-frame trails trace swooping collective paths as brush-stroke formations on black.

## Technical Details
- **Renderer**: P2D
- **Simulation**: Vectorized NumPy, NumPy.
- **Visuals**: persistent trails, bloom-like highlights, dark-field contrast.
- **Animation**: 8 seconds at 60fps

# boid_flock

![Preview](preview_p1.png)

## Metadata
- **Date**: 2026-04-25
- **Theme**: emergence, swarm intelligence, organic motion
- **Technique**: Reynolds boid rules (separation/alignment/cohesion), vectorized numpy physics, heading-based HSV color, circular trail buffer

## Concept
300 boids forming emergent flocks; heading-angle coloring makes each flock a coherent color ribbon; 50-frame trails trace swooping collective paths as brush-stroke formations on black

## Technical Details
- **Renderer**: P2D
- **Simulation**: Reynolds boid rules (separation/alignment/cohesion)
- **Visuals**: vectorized numpy physics, heading-based HSV color, circular trail buffer
- **Animation**: 10s @ 60fps (typical)

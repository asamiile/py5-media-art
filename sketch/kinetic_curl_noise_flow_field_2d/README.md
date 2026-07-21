# kinetic_curl_noise_flow_field_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
An ethereal river of glowing particles sweeping across the canvas. Unlike standard Perlin noise flow fields which often converge into dense lines (sinks), this sketch uses a divergence-free "curl" noise field to ensure particles swirl in continuous, incompressible fluid-like vortexes without ever bunching up.

## Techniques
- **Curl Noise**: A pseudo-curl noise vector field is calculated by taking the cross partial derivatives of a scalar OpenSimplex noise field (`py5.os_noise`). This guarantees divergence-free motion, creating natural-looking turbulence and eddies.
- **Motion Trails**: 15,000 particles are rendered each frame with additive blending (`py5.ADD`). A semi-transparent black rectangle (`fill(5, 5, 15, 10)`) is drawn each frame instead of clearing the background, leaving beautiful fading motion trails that visualize the vector field over time.
- **Animated Z-Slice**: The 3rd dimension of the OpenSimplex noise is slowly incremented each frame, causing the fluid flow to smoothly morph over time.

## Palette
Neon cyan, teal, and magenta on an inky deep blue background.

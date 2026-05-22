# hopf_fibration_projection

**Date**: 2026-05-22
**Format**: 15s 4K/60fps MP4
**Algorithm/Technique**: Parametric 4D generation of Hopf circles projected via Stereographic projection from S3 to R3, and then to 2D. Rendered as luminous, silken threads using an additive blend mode.

## Concept

The mathematical elegance of the Hopf Fibration, projecting the 4D hypersphere onto 3D space as a seamless arrangement of interlocking, luminous circular fibers that rotate endlessly in higher dimensions.

## Implementation Notes

- Leverages pure vectorized NumPy array calculations to efficiently map hundreds of thousands of vertices from 4D space down to a 2D camera projection.
- Applies an isoclinic 4D rotation before stereographic projection, which causes the entire torus structure to smoothly turn inside out without any intersections.
- Rendered in py5's default 2D renderer using `blend_mode(ADD)` to ensure mathematically perfect alpha compositing and antialiasing without relying on headless OpenGL contexts.
- Fibers are colored using an iridescent HSB gradient mapped to their origin coordinates on the S2 base sphere.

# kinetic_lissajous_web_weaver_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
Elegant, sweeping golden ribbons of light tracing intricate 3D Lissajous knots that rotate gracefully in a dark void. The animation weaves an ethereal, glowing 3D shape out of thousands of thin, intersecting threads.

## Techniques
- **3D Lissajous Math**: A complex, multi-frequency 3D parametric equation generates a continuous knot looping through space.
- **Vectorized Projection**: The 3D coordinates are dynamically rotated using custom Euler rotation matrices via `numpy`, then projected onto the 2D canvas with depth scaling. This allows for extremely high point counts (tens of thousands of vertices per frame) at smooth 60fps framerates.
- **Depth-Based Color Mapping**: The z-depth of the rotated points is used to calculate atmospheric falloff. Threads closer to the camera are rendered in bright, hot gold, while threads in the background fade into deep crimsons and low-opacity shadows.

## Palette
Deep crimsons and glowing, bright golds that overlap constructively via additive blending against absolute black.

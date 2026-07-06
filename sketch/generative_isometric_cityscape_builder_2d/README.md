# generative_isometric_cityscape_builder_2d

**Date**: 2026-07-05
**Type**: Animation (10-30s @ 60fps)

## Concept
A procedural pseudo-3D isometric cityscape that constantly builds and rebuilds itself. Skyscrapers rise and fall rhythmically based on multiple overlapping 2D Perlin noise fields, creating the illusion of a breathing metropolis.

## Techniques
Uses a dense grid of 2D quads drawn with an isometric projection offset. The height of each building is driven by moving noise functions. Depth sorting is natively achieved by iterating from back to front.

## Palette
Synthwave sunset. A deep purple background, with buildings transitioning vertically from dark navy to bright magenta and glowing neon orange.

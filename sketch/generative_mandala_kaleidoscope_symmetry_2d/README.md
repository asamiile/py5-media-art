# generative_mandala_kaleidoscope_symmetry_2d

**Date**: 2026-07-07
**Type**: Animation (10-30s @ 60fps)

## Concept
A continuously evolving kaleidoscope mandala. The sketch generates a base pie slice of complex, overlapping curves and particles driven by Perlin noise, and then perfectly mirrors and rotates this slice 12 times around the center to create a dynamic, 12-fold symmetric mandala.

## Techniques
Uses `py5.translate()`, `py5.rotate()`, and `py5.scale(1, -1)` for the kaleidoscopic reflection math. The base shape is drawn using multiple layers of `py5.bezier()` curves whose control points and radii drift through a 3D noise field (`py5.os_noise`). Additive blending (`py5.blend_mode(py5.ADD)`) combined with motion blur makes the mandala shimmer.

## Palette
Iridescent opal. A soft dark background with the mandala shimmering in pearl white, soft pinks, and pale cyans, mapped directly from noise loops to HSB color space.

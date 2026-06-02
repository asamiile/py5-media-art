# Gravitational Wave Line Distortion 2D

## Description
A high-contrast minimalist representation of gravity waves rippling through spacetime. A dense grid of thousands of parallel white lines bends and distorts organically as invisible mass passes through.

## Technical Details
- **Format:** Animation (10s @ 60fps)
- **Palette:** Monochrome (white on black) with subtle spectral highlights (cyan/magenta) at the points of maximum distortion.
- **Algorithm:** 2D vector field displacement. A grid of horizontal lines is drawn, but the Y-coordinates of vertices are heavily displaced by a combination of inverse-square gravity wells (Gaussian distribution) and 2D Perlin noise. The gravity wells slowly orbit a central point.
- **Renderer:** py5.P2D with HSB shading based on total wave displacement.

# kinetic_lissajous_web_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
A mesmerizing geometric illusion created by wrapping thousands of delicate lines around a continuously shifting Lissajous figure. This mimics the classic "string art" craft, but brought to life as a kinetic, pseudo-3D sculpture.

## Techniques
- **Lissajous Base**: An array of 1200 points is calculated over the domain $[0, 2\pi]$ using complex sinusoidal equations for $X$ and $Y$ (with frequency multipliers $5, 4$ and $3, 7$ respectively).
- **Phase Shifting**: The internal phase shifts of the sine waves ($\delta_1, \delta_2$) are incremented every frame. This causes the entire point cloud to smoothly morph and fold in on itself, giving a distinct illusion of 3D rotation.
- **String Art Topology**: Rather than connecting the points sequentially to form a solid line, points are connected across specific array offsets (e.g. $i$ to $i+1$, $i$ to $i+20$, $i$ to $i+150$). Each topological connection layer is given a different vibrant color and drawn with low opacity additive blending.

## Palette
Neon red, electric blue, violet, orange, and stark white on a black canvas.

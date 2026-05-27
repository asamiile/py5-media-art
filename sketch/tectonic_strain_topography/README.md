# tectonic_strain_topography

**Date**: 2026-05-26
**Format**: Animation (15s @ 60fps)

## Concept
A dynamic 3D topographic map showing shifting fault lines and stress accumulation, glowing in thermal reds and cool blues.

## Technique
Uses a 3D `py5.QUAD_STRIP` mesh deformed by `py5.noise()` for the base terrain. A central fault line is animated using a sine wave offset, splitting the mesh into two dynamically shifting tectonic plates. The color and lighting adapt dynamically to the simulated strain (shift magnitude) to highlight areas of high stress.

## Notes
- Initially attempted to use the external `noise` package, but rewrote to use native `py5.noise()` to avoid dependency issues.
- Rendered to 3840x2160 MP4.

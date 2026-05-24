# crystal_dislocation_glide

**Date**: 2026-05-22
**Format**: 15s 4K/60fps MP4
**Algorithm/Technique**: Vectorized 2D Sine-Gordon (Frenkel-Kontorova) phase-field model. Computes atomic displacement under macroscopic shear stress with local yielding and dislocation avalanches. Real-time substepping with additive phonon/core color mapping directly into the py5 pixel buffer.

## Concept

The sudden, violent slipping of microscopic lattice defects through an atomic crystal under immense pressure, visualizing the invisible physics of plastic deformation.

## Implementation Notes

- Employs a 2D scalar wave equation with a periodic sine potential `F_sub = -A * sin(u)` to mathematically enforce discrete lattice spacing.
- Incorporates dynamic thermal noise and fixed "precipitates" to pin expanding dislocation loops, causing rich avalanche behaviors.
- The color scheme maps physical phenomena directly: background atomic lattice (Ice Blue), kinetic energy/phonons (Amethyst), and defect cores/stacking faults (Blinding Amber).
- Direct frame-buffer updating via `py5.np_pixels` allows high-resolution physics solving at interactive framerates.

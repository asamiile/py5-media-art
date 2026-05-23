# ginzburg_landau_spiral_defects

**Date**: 2026-05-22
**Format**: 15s 4K/60fps MP4
**Algorithm/Technique**: Vectorized 2D simulation of the Complex Ginzburg-Landau Equation (CGLE). Visualizes the spontaneous emergence of topological defects and rotating spiral waves.

## Concept

The mesmerizing, spontaneous emergence of rotating spiral waves and topological defects in a complex oscillatory medium, modeling phenomena ranging from chemical clocks (like the Belousov-Zhabotinsky reaction) to quantum superconductivity.

## Implementation Notes

- Employs a high-performance finite difference time domain (FDTD) solver in pure NumPy to compute the nonlinear evolution of the complex scalar field $A(x,y,t)$.
- Resolves complex numbers into a vibrant custom synthwave colormap (Cyan, Magenta, Gold, Emerald) by mapping the complex phase $angle(A)$ directly to hue interpolation.
- Emphasizes topological defects (spiral wave centers) as deep, pitch-black voids by scaling brightness aggressively against the amplitude $|A|^3$.
- Uses NumPy's `np.repeat` to efficiently upscale the 960x540 simulation domain to 4K/1080p outputs directly in the py5 pixel buffer.

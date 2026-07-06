# kinetic_fluid_smoke_advection_2d

**Date**: 2026-07-05
**Type**: Animation (10-30s @ 60fps)

## Concept
A generative fluid simulation of dense, luminescent smoke advecting across the canvas. A hidden density field drives the flow, with smoke continually injected from multiple moving emitters. It forms beautiful swirling eddies and dissipating trails.

## Techniques
Solves a lightweight Eulerian fluid simulation (Navier-Stokes) on a lower-resolution grid to keep performance at 60fps. The velocity field advects the density field, and then the density field is mapped to Py5's `np_pixels` with bilinear interpolation for a smooth, organic appearance.

## Palette
Neon gas. A dark navy void, with dense smoke glowing in vivid pink, electric blue, and toxic green, slowly cooling to dark purple as it dissipates.

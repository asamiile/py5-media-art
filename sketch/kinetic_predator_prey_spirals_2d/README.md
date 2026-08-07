# kinetic_predator_prey_spirals_2d

![Preview](kinetic_predator_prey_spirals_2d_p1.png)

## Metadata
- **Date**: 2026-08-06
- **Theme**: Spatial Lotka-Volterra dynamics, predator-prey systems, spiral waves, biological self-organization
- **Technique**: Vectorized 2D NumPy finite-difference Laplacian (using fast grid rolling), Euler integration of Lotka-Volterra PDEs, custom RGB blend mapping, direct memory pixel blitting (`np_pixels`), vignette shadow, telemetry HUD.

## Concept
A 4K kinetic visualization of the classic predator-prey (Lotka-Volterra) equations simulated on a 2D spatial grid. Because the populations can diffuse (move) across the domain, the localized oscillations stabilize into complex self-organizing structures, including traveling fronts and rotating spiral waves.

The visualization maps prey (glowing green/mint) and predators (glowing coral/magenta) to overlapping RGB channels on a deep black background. The areas where they actively interact form hot white highlights representing high-energy predation events. The resulting grid is upscaled and written directly to the screen memory via py5's `np_pixels` interface to achieve high-performance rendering.

## Technical Details
- **Renderer**: Java2D
- **Simulation**: Spatial Lotka-Volterra system with carrying capacity, predation efficiency, and predator mortality, computed vectorially in NumPy via fast 5-point stencil Laplacian. Runs 4 steps per frame on a 480x270 grid.
- **Visuals**: Direct `np_pixels` memory blitting, custom color mapping, vignette frame overlay, and technical telemetry HUD.
- **Animation**: 15 seconds @ 60 FPS (900 frames)

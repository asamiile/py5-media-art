# abstract_fluid_marbling

## Metadata
- **Date**: 2026-05-23
- **Theme**: A generative simulation of Suminagashi (Japanese fluid marbling art), created entirely with mathemat
- **Technique**: Unknown
- **Logic Lab Reference**: 

## Concept
A generative simulation of Suminagashi (Japanese fluid marbling art), created entirely with mathematically deformed lines.

- **Date**: 2026-05-23
- **Theme**: Fluid marbling, suminagashi, marble paper, organic flow, vector field advection.
- **Technique**: Instead of simulating a raster pixel grid, this sketch renders 120 horizontal vector lines, each containing 400 vertices. To simulate the swirling, organic eddies of ink dropped onto water, every vertex is displaced (`dx`, `dy`) by a combination of overlapping 3D Perlin noise fields. By carefully tuning the frequency and amplitude of the noise functions, the lines are pulled and folded into elegant, continuous swirls that perfectly mimic fluid advection without the extreme computational overhead of a true Navier-Stokes solver. Rendered in P2D with a smooth ocean-blue to deep-purple gradient. 15s 60fps MP4.
- **Description**: Dense, horizontal lines of cyan and purple ink are suspended in a dark void. Slowly, invisible currents begin to stir the fluid. The perfectly straight lines are drawn into complex, curling eddies, folding over themselves like marble patterns on expensive paper. The fluid motion is incredibly smooth and organic, continuously twisting into new, mesmerizing fractal swirls before gently drifting off-screen.

## Technical Details
- **Renderer**: P2D
- **Simulation**: Unknown
- **Visuals**: Unknown
- **Animation**: Contains animation details

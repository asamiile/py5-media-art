# abstract_reaction_diffusion_slime

## Metadata
- **Date**: 2026-05-24
- **Theme**: A highly optimized mathematical simulation of cellular growth using the Gray-Scott Reaction-Diffusio
- **Technique**: Unknown
- **Logic Lab Reference**: 

## Concept
A highly optimized mathematical simulation of cellular growth using the Gray-Scott Reaction-Diffusion model.

- **Date**: 2026-05-23
- **Theme**: Biology, cellular division, slime mold, Reaction-Diffusion, organic patterns, Turing patterns.
- **Technique**: Solves the Gray-Scott Reaction-Diffusion differential equations natively in Python. To achieve 60fps performance without shaders, the simulation runs at half-resolution ($960 \times 540$) using highly optimized 2D NumPy array slicing for the discrete Laplacian convolution operator. The simulation is advanced 8 steps per drawn frame. The resulting chemical concentration fields are then upscaled via `numpy.repeat` and mapped to a custom color gradient, which is blasted directly to the screen buffer via `py5.np_pixels`. 15s 60fps MP4.
- **Description**: A macroscopic view of an alien cellular organism dividing and multiplying in a petri dish. Starting from a few microscopic seeds, neon cyan and green chemical trails rapidly spread outward across a dark violet void. The organic patterns undergo continuous mitosis, splitting into maze-like ridges, coral-like branches, and leopard spots as the two simulated chemicals continuously react and diffuse into one another.

## Technical Details
- **Renderer**: Unknown
- **Simulation**: Unknown
- **Visuals**: Unknown
- **Animation**: Contains animation details

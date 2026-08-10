# kinetic_kpz_interface_roughening_2d

A 4K kinetic visualization of stochastic interface growth and kinetic roughening, solving the 2D Kardar-Parisi-Zhang (KPZ) equation to simulate mineral deposition onto a cold obsidian substrate.

## Simulation Details

- **KPZ PDE Solver**: Explicit numerical integration of the 2D Kardar-Parisi-Zhang equation combining surface tension diffusion (Laplacian smoothing), non-linear growth gradient expansion ($\frac{\lambda}{2} (\nabla h)^2$), and Gaussian white noise.
- **High-Performance Shading**: Normal mapping, Blinn-Phong specular reflections, color interpolation, and contour generation computed on the low-resolution simulation grid ($480 \times 270$) for maximum efficiency, upscaling the final color matrices to 4K ($3840 \times 2160$) before rendering.
- **Visual Mapping**: Valleys are mapped to deep amethyst, slopes to warm amber gold, and peaks to bright cyan specular highlights, highlighted by neon glowing concentric contour veins.

## Run

To run the simulation and render the 20-second animation:

```bash
uv run python sketch/kinetic_kpz_interface_roughening_2d/main.py
```

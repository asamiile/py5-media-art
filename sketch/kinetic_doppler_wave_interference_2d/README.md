# kinetic_doppler_wave_interference_2d

A 4K kinetic fluid simulation solving the 2D Wave Equation using Finite-Difference Time-Domain (FDTD) wave propagation to visualize the acoustic Doppler effect and interference wakes of three orbiting probes.

## Simulation Details

- **FDTD Wave Solver**: Numerical integration of the 2D wave equation with viscous damping, allowing constructive and destructive wave interference.
- **Dynamic Orbital Sources**: Three wave emitters orbiting in circular, Lissajous, and figure-8 trajectories. The wave sources are smoothly injected using a Gaussian footprint to prevent spatial aliasing.
- **Chromatic Liquid Shading**: Low-resolution simulation upscaled to 4K using bilinear interpolation. The displacement is shaded with custom normal-mapped specular lighting (Blinn-Phong) to map troughs to deep cobalt blue, slopes to phosphor mint, and crests to solar gold.

## Run

To run the simulation and render the 20-second animation:

```bash
uv run python sketch/kinetic_doppler_wave_interference_2d/main.py
```

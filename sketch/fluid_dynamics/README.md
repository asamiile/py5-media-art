# Fluid Dynamics

A mathematical fluid simulation revealing the hidden patterns of flow and turbulence through Navier-Stokes equations.

## Technique

Navier-Stokes-based fluid dynamics simulation with vorticity visualization. Uses a stable fluid solver with dye advection, diffusion, projection (to make velocity field divergence-free), and vorticity confinement to create organic swirling patterns. The simulation runs on a 100×100 grid and renders to 1920×1080 canvas.

## Color Palette

- Background: Deep ocean navy (#0a1628)
- Dominant (60%): Electric cyan (#00d4ff) with varying intensity
- Secondary (30%): Warm coral (#ff6b6b) for contrast
- Accent (10%): Golden amber (#ffd93d) for highlights
- Mood: Cold/precise

## Visual Impression

A mesmerizing display of swirling fluid currents where mathematical equations create organic, flowing patterns that resemble ocean currents or atmospheric flow. Electric cyan and warm coral colors dance across a deep navy background, with golden amber highlights adding depth and visual interest.

## Parameters

- GRID_SIZE = 100 (simulation grid resolution)
- ITERATIONS = 10 (Gauss-Seidel solver iterations)
- DT = 0.1 (time step)
- DIFFUSION = 0.0001 (diffusion rate)
- VISCOSITY = 0.0001 (fluid viscosity)
- VORTICITY_STRENGTH = 0.05 (vorticity confinement strength)
- 8 initial swirling sources with random positions
- 50 simulation steps before rendering

## Running

```bash
uv run python sketch/fluid_dynamics/main.py
```

## Output

- `preview.png` — 1920×1080 preview image
- Change `SIZE` constant in `main.py` for 3840×2160 output

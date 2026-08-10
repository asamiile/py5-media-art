# kinetic_shallow_water_equations_2d

A 4K kinetic fluid simulation solving the 2D Shallow Water Equations (SWE) on a dynamically perturbed, shallow fluid basin with complex bottom bathymetry.

## Simulation Details

- **Equations Solver**: Explicit finite difference integration of mass continuity and momentum equations with bottom bathymetry $b(x, y)$, Coriolis parameters $f$ (adding rotational/gyre-like currents), and bottom friction $r$.
- **Stabilization**: Artificial viscosity (Laplacian smoothing) added to the height and velocity fields to maintain stability without a staggered grid.
- **Rendering**: Real-time normal mapping computed from surface height gradients $\nabla(h + b)$, combined with Phong specular specular highlights (using a virtual directional light source) to simulate a deep ocean/liquid platinum surface.
- **HUD Layout**: Telemetry reporting physical parameters, coordinate metrics, and current frame render progress.

## Run

To run the simulation and render the 15-second animation:

```bash
uv run python sketch/kinetic_shallow_water_equations_2d/main.py
```

# kinetic_cahn_hilliard_spinodal_decomposition_2d

A 4K kinetic fluid simulation solving the 2D Cahn-Hilliard equation to visualize spinodal decomposition—the spontaneous phase separation of a homogeneous binary mixture into separate domain states over time.

## Simulation Details

- **Cahn-Hilliard PDE Solver**: Numerical integration of the fourth-order Cahn-Hilliard equation using finite difference Laplacians for concentration $\phi$ and chemical potential $\mu = \phi^3 - \phi - \gamma \nabla^2 \phi$.
- **Boundary Gradient Detection**: Interface boundaries are identified by calculating spatial gradients of the concentration field, rendering a bright golden neon glow outlining the separation borders.
- **Normal-Mapped Lighting**: Shaded with custom normal-mapped specular lighting (Blinn-Phong) to map concentration values to cobalt blue (Phase A) and coral orange (Phase B) droplets rising out of a deep purple void.

## Run

To run the simulation and render the 20-second animation:

```bash
uv run python sketch/kinetic_cahn_hilliard_spinodal_decomposition_2d/main.py
```

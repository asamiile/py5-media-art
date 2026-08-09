# kinetic_polycrystalline_grain_growth_2d

A 4K kinetic material science simulation demonstrating polycrystalline grain growth, grain boundary migration, and periodic dynamic recrystallization.

## Physical Mechanism

- **Model**: Vectorized 2D Monte Carlo Potts model with $Q = 32$ initial grain orientations, evolving using Metropolis dynamics under a decreasing temperature schedule (simulating annealing).
- **Recrystallization**: Periodically injects fresh circular nuclei of a new, highly-stressed crystal phase, which grow and consume older, relaxed grains.
- **Rendering**: Grains are mapped to a custom high-contrast palette. Boundaries between domains are identified and rendered with a glowing neon amber overlay, mimicking energy dissipation at grain interfaces.
- **Technical HUD**: Displays the current frame, system annealing temperature, total phase IDs, and system status.

## Run

To run the simulation and render the 15-second animation:

```bash
uv run python sketch/kinetic_polycrystalline_grain_growth_2d/main.py
```

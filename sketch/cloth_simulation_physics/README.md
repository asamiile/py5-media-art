# cloth_simulation_physics

![Preview](cloth_simulation_physics_p1.png)

## Metadata
- **Date**: 2026-05-23
- **Theme**: A real-time physics simulation of a glowing digital cloth billowing in simulated wind
- **Technique**: Unknown
- **Logic Lab Reference**: 

## Concept
A real-time physics simulation of a glowing digital cloth billowing in simulated wind.

- **Date**: 2026-05-23
- **Theme**: Physical simulation, Verlet integration, fabric dynamics, neon cyber-aesthetics.
- **Technique**: Uses NumPy to compute Verlet integration physics for a 50x50 grid of connected nodes (2,500 total particles). The grid enforces structural spring constraints to maintain its shape, with the top edge pinned in space. Gravity constantly pulls the nodes downward, while a 3D Perlin noise field applies a continuous, turbulent "wind" force, pushing the fabric backwards. The cloth is rendered in P3D using `py5.QUADS`, mapping the Z-depth (how far the wind pushes the fabric) and the X/Y coordinates directly to the HSB color wheel. 15s 60fps MP4.
- **Description**: A massive, brilliantly colored neon sheet hangs suspended in a dark void. As an invisible digital wind strikes it, the fabric ripples, folds, and violently billows backwards, throwing off a mesmerizing gradient of shifting rainbow colors that highlight every wrinkle and fold of the simulated cloth.

## Technical Details
- **Renderer**: P3D
- **Simulation**: Unknown
- **Visuals**: Unknown
- **Animation**: Contains animation details

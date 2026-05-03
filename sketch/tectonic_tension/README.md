# tectonic_tension

A visualization of the immense geological forces at work beneath the Earth's crust, where shifting plates collide and release primal energy.

## Concept
This work simulates the dynamics of plate tectonics using a Voronoi-based decomposition of a 2D surface. It explores the tension that builds up at the boundaries of these plates as they drift, collide, and slide past one another, resulting in glowing rifts and volcanic emissions.

## Technique
- **Voronoi Plate Simulation**: 32 moving sites define the boundaries of geological plates using `scipy.spatial.Voronoi`.
- **Boundary Stress Analysis**: Relative velocities between adjacent plate centers determine the "tension" at each ridge.
- **Multi-Layered Glow Synthesis**: Boundaries are rendered with additive blending and multiple layers of varying width and transparency to simulate the intense heat of magma.
- **Kinetic Ejecta**: Magma particles are spawned at boundaries with velocities derived from plate motion and ridge normals.
- **Atmospheric Haze & Grain**: A combination of highly transparent elliptical gradients and global pixel noise creates a visceral, volcanic atmosphere.

## Files
- `main.py`: The simulation logic and rendering engine.
- `output.mp4`: A 5-second 60fps animation of the shifting plates.
- `preview.png`: A high-resolution snapshot of the tectonic tension.

# abstract_particle_spring_physics_mesh

A digital soft-body physics simulation of a highly elastic wireframe fabric being deformed by invisible colliders.

- **Date**: 2026-05-23
- **Theme**: Soft-body physics, Hooke's Law, digital fabric, spring constraints, interactive topology, tearing force.
- **Technique**: A 60x40 2D grid of particles is simulated using basic Euler integration and Hooke's Law. Each particle is connected to its rest position via a mathematical spring ($F = -kx$). Three invisible circular colliders move in complex Lissajous patterns across the screen, colliding with the grid particles and forcefully pushing them away. When the colliders pass, the springs rapidly snap the particles back into place with elastic damping. The connections between particles are drawn as lines using additive blending (`py5.ADD`). The color, brightness, and opacity of each line segment are directly mapped to its "stretch factor"—lines glow white-hot when under extreme tension. 15s 60fps MP4.
- **Description**: A dense, dark wireframe mesh resembling digital fabric spans the entire screen. Suddenly, invisible spheres crash into the fabric from behind, stretching the grid violently. The areas of the mesh under extreme physical tension glow brightly in blinding cyan and magenta, visualizing the kinetic energy of the impact. As the invisible forces move away, the fabric snaps back, rippling with residual elastic waves until it settles back into its perfect, dormant grid.

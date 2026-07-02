# Kinetic Gravitational Lensing Accretion Disk 2D

## Concept
A massive black hole distorts an accretion disk of 150,000 glowing particles. The immense gravity warps the trajectories and the spatial field around it. A fake 3D perspective creates a dramatic tilted orbital plane.

## Technical Implementation
- Newtonian 2D physics simulation of particles orbiting a massive central attractor ($F = G \frac{M}{r^2 + \text{softening}^2}$).
- Initial positions and velocities are generated to form a stable (yet turbulent) accretion disk.
- Fake 3D perspective is achieved by squishing the Y-axis coordinates during rendering, but restoring them during physics calculations to ensure accurate circular orbital mechanics.
- A faint amount of drag is applied so particles slowly spiral into the event horizon.
- Particles are split into 3 speed percentiles, mapping color from deep red (slow outer rim) to glowing cyan/white (fast inner disk) to simulate relativistic blue-shifting and immense heat.

## Execution
- `Particles`: 150,000
- `FPS`: 60
- `Duration`: 15 Seconds
- `Resolution`: 3840x2160

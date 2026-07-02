# kinetic_galaxy_n_body_collision_2d

![Preview](kinetic_galaxy_n_body_collision_2d_p1.png)

## Metadata
- **Date**: 2026-06-28
- **Theme**: An N-body gravitational simulation of two massive colliding galaxies
- **Technique**: Evaluating the gravitational forces of $N=4,000$ particles means computing an enormous $4,000 \times 4,000$ pairwise distance matrix every single frame using pure NumPy. Because gravity follows the $1/r^2$ inverse-square law, particles can experience infinite acceleration if they get too close to one another, so a mathematical "softening" parameter is added to the denominator to prevent singularities and chaotic numerical explosions.
- **Logic Lab Reference**: 

## Concept
An N-body gravitational simulation of two massive colliding galaxies. Each galaxy is built as a rotating disk of particles, and they are hurled toward each other to simulate an epic gravitational collision. As they pass through one another, the gravitational tidal forces rip long, beautiful spiral arms and tails out of the original disks.

## Technical Details
- **Renderer**: Unknown
- **Simulation**: Unknown
- **Visuals**: Unknown
- **Animation**: Contains animation details

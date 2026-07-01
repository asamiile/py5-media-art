# kinetic_galaxy_n_body_collision_2d

## Concept
An N-body gravitational simulation of two massive colliding galaxies. Each galaxy is built as a rotating disk of particles, and they are hurled toward each other to simulate an epic gravitational collision. As they pass through one another, the gravitational tidal forces rip long, beautiful spiral arms and tails out of the original disks.

## Technique
Evaluating the gravitational forces of $N=4,000$ particles means computing an enormous $4,000 \times 4,000$ pairwise distance matrix every single frame using pure NumPy. Because gravity follows the $1/r^2$ inverse-square law, particles can experience infinite acceleration if they get too close to one another, so a mathematical "softening" parameter is added to the denominator to prevent singularities and chaotic numerical explosions.

## Palette
- **Base**: Deep space fading background
- **Galaxies**: Deep glowing blue/cyan for one galaxy, bright fiery orange/red for the other. Additive blending creates intense white/purple energy flashes where they intersect.
- **Mood**: Epic, cosmic, fluid, fiery, chaotic

## Format
Animation (450 frames @ 30fps)

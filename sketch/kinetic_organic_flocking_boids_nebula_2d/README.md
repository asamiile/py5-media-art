# kinetic_organic_flocking_boids_nebula_2d

2,500 glowing particles (boids) flocking in a 2D space, exhibiting collective behavior and leaving a fading trail. They behave like a fluid, intelligent nebula or a giant swarm of deep-sea bioluminescence.

## Techniques

A highly optimized, fully vectorized flocking algorithm using SciPy's `cKDTree.sparse_distance_matrix` to compute nearest neighbors extremely fast. The density of the flock dynamically changes each boid's color in real time.

## Palette

"Nebula" colors: Deep space blues and purples in sparse areas, shifting up to hot pink and bright cyan in densely packed clusters.

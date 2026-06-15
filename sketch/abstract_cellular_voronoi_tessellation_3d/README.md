# abstract_cellular_voronoi_tessellation_3d

An animated 15s sequence of a 3D animation of shifting Voronoi cells that look like microscopic tissues or alien geology.

## Theme
A 3D animation of shifting Voronoi cells that look like microscopic tissues or alien geology. The cells slowly shift upwards like mountains and then descend.

## Technique
A grid of 3D triangle strips is generated. For each point on the grid, the distance to the nearest of N moving seed points is calculated (a basic Voronoi distance). That distance is mapped to the Z height of the 3D grid, creating cellular peaks. The seed points drift smoothly across the field using `py5.os_noise`. Additive lighting and neon colors give it a vibrant, organic look.

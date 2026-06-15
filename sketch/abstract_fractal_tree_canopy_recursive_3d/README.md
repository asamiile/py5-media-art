# abstract_fractal_tree_canopy_recursive_3d

An animated 20s sequence of a 3D recursive fractal tree structure where the camera slowly orbits and zooms through the branches, which glow with shifting colors.

## Theme
A 3D recursive fractal tree structure where the camera slowly orbits and zooms through the branches, which glow with shifting colors.

## Technique
A recursive function `draw_branch()` draws lines that progressively scale down and rotate, creating an organic tree shape up to a depth of 7. The angles of branching are driven by `py5.os_noise`, creating a swaying, living canopy. The camera (`py5.camera`) slowly orbits the structure in 3D space. Additive blending (`py5.ADD`) and depth-based coloring give the fractal tree a majestic, luminous presence against a dark forest-green background.

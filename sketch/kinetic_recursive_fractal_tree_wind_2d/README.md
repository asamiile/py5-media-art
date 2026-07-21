# kinetic_recursive_fractal_tree_wind_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
A glowing forest of recursive, bioluminescent fractal trees. The intricate canopies sway and flex fluidly, simulating an organic, invisible mathematical wind blowing through dense alien flora.

## Techniques
- **Deep Recursion**: The trees are generated using a recursive function that branches 14 levels deep, producing over 16,000 individual branch strokes per tree.
- **Perlin Wind**: The angle of each branch is offset dynamically using a 2D Perlin noise field parameterized by time and the branch index/depth. The base of the tree barely moves, while the dense outer canopies flutter rapidly.
- **Additive Bioluminescence**: Using `py5.blend_mode(py5.ADD)`, the hundreds of thousands of overlapping, thin lines constructively interfere to produce intensely bright, glowing canopy cores.

## Palette
Bioluminescent cyan, aqua, and deep blues. The branches start dark and get brighter and whiter towards the leaves, layered on a deep black background with a faint motion-blur trail.

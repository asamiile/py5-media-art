# pulsating_crystal_lattice_heart_3d

A mesmerizing 3D lattice of interconnected geometric nodes that rhythmically expand and contract, pulsating with energy like a living crystal heart.

![Preview](pulsating_crystal_lattice_heart_3d_p1.png)

## Technique

A dense 3D grid of boxes whose sizes are modulated by both 3D OpenSimplex noise and a sinusoidal pulsing function driven by frame count. Nodes outside a defined spherical radius are culled to form a glowing core shape. Additive blending and dynamic HSB coloring give it the crystal energy look.

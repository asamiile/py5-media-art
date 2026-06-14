# bioluminescent_deep_sea_jellyfish_3d

An animated 20s sequence of a 3D bioluminescent jellyfish floating gracefully in a deep ocean, with pulsing translucent neon gradients and flowing tentacles.

## Theme
A 3D animation of a bioluminescent jellyfish floating gracefully in a deep, dark ocean, with pulsing translucent neon gradients and flowing tentacles.

## Technique
3D modeling using py5 primitives. The bell of the jellyfish is a hemisphere made using `py5.begin_shape(py5.TRIANGLE_STRIP)` with spherical coordinates that ripple over time using a sine wave. The tentacles are drawn using multiple `py5.curve_vertex` points that lag behind the main body's movement (simulated using delayed sine waves). Additive blending and glowing cyan/purple colors are used to simulate bioluminescence.

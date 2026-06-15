# cybernetic_holographic_data_sphere_3d

An animated 20s sequence of a 3D wireframe sphere that looks like a high-tech holographic data core, with rings of floating data points orbiting it, shifting rapidly like a futuristic UI element.

## Theme
A 3D wireframe sphere that looks like a high-tech holographic data core, with rings of floating data points orbiting it, shifting rapidly like a futuristic UI element.

## Technique
`py5.begin_shape(py5.LINES)` is used to draw a sphere built from lat/long segments, but many segments are dropped randomly using noise (`py5.os_noise`) to make it look fragmented and glitchy. Rings of small rectangles orbit the sphere. A neon cyan and orange color palette on a pure black background is used with additive blending for a glowing holographic effect.

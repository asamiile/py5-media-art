# retro_synthwave_neon_grid_sun_3d

An animated 15s sequence of a retro-futuristic synthwave-inspired 3D landscape with a scrolling glowing wireframe grid terrain over a dark sky. A bright glowing sun with horizontal cuts sets in the background.

## Theme
A retro-futuristic synthwave-inspired 3D landscape.

## Technique
3D rendering using `py5.P3D`. The terrain is generated using a triangle strip mapped to Perlin noise (`py5.os_noise`) which shifts along the y-axis over time to simulate forward motion. The terrain attenuates into a valley shape. The background sun is drawn as 2D slices without depth to give a stylized 80s graphic look, with slices scrolling upwards and cutting out near the bottom.

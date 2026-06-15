# retro_pixel_art_isometric_cityscape_2d

An animated 15s sequence of a scrolling 2D isometric pixel-art cityscape with glowing neon tops.

## Theme
A scrolling isometric cityscape with retro-wave synth aesthetics, where buildings vary in height driven by Perlin noise.

## Technique
Isometric 2D math (`x = (c - r) * w`, `y = (c + r) * h/2 - z`) is used to project cubes in a 3D space from back to front using a painter's algorithm. The heights of the cubes are mapped from `py5.os_noise` which shifts over time to create a continuous scrolling effect. Taller buildings have cyan to pink glowing tops.

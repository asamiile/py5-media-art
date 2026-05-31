# cyberpunk_neon_terrain_flyover_3d

## Theme
A high-speed flight over an alien cyber-landscape composed of a glowing wireframe terrain, split by a flat data highway running down the center.

## Technique
A massive 3D grid mapped via `py5.begin_shape(py5.TRIANGLE_STRIP)`. The Z-height of each vertex is governed by 3D OpenSimplex noise. By tracking a circular path through the 2nd and 3rd dimensions of the noise space across frames, the terrain continuously undulates and flows towards the camera while guaranteeing a perfectly seamless 10-second loop.

## Color palette
- Background: Very dark synthwave purple
- Dominant: Neon magenta / Hot pink
- Secondary: Electric cyan grid lines
- Mood: Retro-futuristic / Cyberpunk / Synthwave

## Format
Animation (10s @ 60fps)

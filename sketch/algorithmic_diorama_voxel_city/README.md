# algorithmic_diorama_voxel_city

A procedurally generated, 3D voxel-style cyberpunk city floating in a dark void.

- **Date**: 2026-05-23
- **Theme**: Procedural generation, isometric diorama, voxel art, cyberpunk cityscape.
- **Technique**: A $30 \times 30$ grid of 3D boxes is generated during `setup()` using 2D Perlin noise combined with a radial distance envelope. This forces the tallest "skyscrapers" to cluster in the center of the grid, tapering off into smaller buildings near the edges to create a distinct floating island diorama. The height values are quantized to give a blocky, voxel aesthetic. During `draw()`, the camera is positioned and rotated to create a high-angle isometric-style perspective. The buildings dynamically pulse in height slightly over time, and random 3D Perlin noise is used to make individual buildings flash brightly, simulating glowing neon windows in a living, breathing cyberpunk city. 15s 60fps MP4.
- **Description**: A dense, futuristic mini-city sits on a thick, dark platform floating in empty space. The buildings are rendered as sleek geometric blocks that transition in color from deep oceanic blues at the edges to vibrant magenta and purple at the towering center. The entire diorama slowly rotates on a turntable, while individual skyscrapers blink and pulse with internal neon light, giving the impression of a living, microscopic metropolis.

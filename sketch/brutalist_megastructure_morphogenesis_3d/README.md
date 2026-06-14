# brutalist_megastructure_morphogenesis_3d

An infinite, procedural brutalist megastructure built from thousands of floating, interlocking concrete-textured blocks that slowly assemble and disassemble themselves in a low-gravity environment.

## Technique

A dense 3D grid of boxes. Using 3D Perlin noise (`py5.os_noise`), the scale and presence of each box are determined. The 3D noise field translates through space, causing the megastructure to appear as if it is endlessly morphing. Harsh directional lighting simulates concrete architectural shading.

## Output

Animation (20s @ 60fps)

# Fluid Cellular Mitosis 3D

## Description
A microscopic view of an alien memory cell dividing and rapidly growing intricate patterns across its glowing membrane. The animation visualizes the biological process of mitosis combined with fluid dynamics and cellular automata.

## Technical Details
- **Format:** Animation (10s @ 60fps)
- **Palette:** Very dark purple/black background with bioluminescent lime, electric violet, and crimson points.
- **Algorithm:** 3D metaball scalar field constructed via distance functions to two separating centers, mapped with 3D Perlin noise to create an organic, bubbling membrane. The surface is rendered using a massive point cloud array based on a Fibonacci sphere distribution.
- **Renderer:** py5.P3D with HSB stroke brightness mapped to the scalar field density.

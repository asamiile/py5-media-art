# kinetic_voronoi_cellular_tessellation_2d

**Date**: 2026-07-07
**Type**: Animation (10-30s @ 60fps)

## Concept
A generative simulation of a Voronoi diagram where the seed points are moving organically in a flow field. As the seeds drift, the cellular boundaries warp and shift like a living microscopic tissue or shimmering soap bubbles.

## Techniques
Uses `scipy.spatial.Voronoi` to calculate the exact distance field polygons for 400 seed points every frame. To ensure perfect clipping at the screen boundaries without elongated edge artifacts, 4 sets of mirror points are dynamically added across the screen's edges. The seed points are displaced continuously using 2D Perlin noise (`py5.os_noise`) to create fluid, organic motion.

## Palette
Iridescent soap bubble. A dark slate background with the Voronoi cells filled with shifting, translucent pastel gradients (cyan, magenta, yellow) that shimmer as the polygons morph. The cell walls are drawn with sharp, bright white lines.

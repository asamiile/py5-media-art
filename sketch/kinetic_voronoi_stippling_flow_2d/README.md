# kinetic_voronoi_stippling_flow_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
A fluid-like mosaic of shifting Voronoi cells sliding past each other. The structure resembles an underwater biological cross-section or a liquid stained-glass window, constantly reforming as the underlying seed points drift.

## Techniques
- **Vector Flow Field**: 1200 seed points are driven across the canvas by a trigonometric interference noise field (sine/cosine functions). This gives them a smooth, organic, fluid motion.
- **Bounded Voronoi Diagram**: On every frame, the points are mirrored across the edges of the screen before passing them to `scipy.spatial.Voronoi`. This classic technique ensures that the Voronoi cells on the edge of the screen remain bounded and closed, rather than stretching to infinity.
- **Area-Based Coloring**: The area of each resulting polygonal cell is calculated using the Shoelace formula. Smaller, denser clusters of cells glow brightly, while larger empty regions fade into darkness.

## Palette
Deep oceanic blues and glowing cyans/teals, reinforcing the liquid, aquatic aesthetic.

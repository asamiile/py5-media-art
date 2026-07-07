# kinetic_recursive_voronoi_shatter_2d

**Date**: 2026-07-07
**Type**: Animation (10-30s @ 60fps)

## Concept
A recursive Voronoi diagram that continuously shatters inward, revealing deeper levels of detail. The cells drift slowly and morph, while the camera slowly zooms in continuously to maintain a constant scale, creating a fractal-like dive.

## Techniques
Uses a dynamic set of points for a Voronoi diagram. As the camera zooms by scaling the point coordinates away from the origin, points that go off-screen are removed, and new points are generated near the center. The edges are drawn with glowing lines, and the cells are filled with shifting, semi-transparent gradients.

## Palette
High contrast neon cyberpunk. Deep purples, electric pinks, and bright cyan against a dark background.

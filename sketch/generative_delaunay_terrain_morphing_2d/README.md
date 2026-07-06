# generative_delaunay_terrain_morphing_2d

**Date**: 2026-07-06
**Type**: Animation (10-30s @ 60fps)

## Concept
A 2D projection of a 3D terrain built from Delaunay triangulation. The terrain heights are driven by 3D Perlin noise that shifts over time, causing the mountains to smoothly morph and roll like waves.

## Techniques
Generates a grid of points, displaces them based on noise, and triangulates using scipy.spatial.Delaunay. The triangles are filled with colors mapped to their average height, creating a low-poly aesthetic.

## Palette
Synthwave sunset. Deep purple and neon blue valleys transitioning to hot pink and vibrant orange peaks against a dark sky.

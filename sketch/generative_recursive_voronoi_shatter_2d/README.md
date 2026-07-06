# generative_recursive_voronoi_shatter_2d

**Date**: 2026-07-05
**Type**: Animation (10-30s @ 60fps)

## Concept
A plane of color is shattered into a Voronoi diagram. The cell centers slowly drift. Periodically, the largest cells shatter into smaller Voronoi diagrams recursively, creating a fractal-like breaking pattern reminiscent of cracked glass or dry earth.

## Techniques
Uses scipy.spatial.Voronoi to generate the cell polygons from a set of moving points. New points are added dynamically over time into regions with low point density.

## Palette
Monochromatic architectural. Clean white background with fine, sharp black lines. Slowly, some cells fill with desaturated ochre or slate blue.

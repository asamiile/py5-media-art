# generative_differential_line_growth_2d

**Date**: 2026-07-05
**Type**: Animation (10-30s @ 60fps)

## Concept
A single closed line that slowly expands, folds, and crumples into itself like a brain coral or a living organism. It mimics cellular growth in a confined space.

## Techniques
Differential growth algorithm using numpy and scipy.spatial.cKDTree. A list of nodes connected by springs. Nodes experience a repulsive force from all other nearby nodes, but an attractive force to their immediate neighbors. New nodes are periodically inserted between adjacent nodes that stretch too far apart.

## Palette
Monochromatic organic. A clean, off-white background with a thin, intricate, dark charcoal line that grows continuously, overlapping into complex moiré patterns.

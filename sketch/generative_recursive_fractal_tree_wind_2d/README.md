# generative_recursive_fractal_tree_wind_2d

**Date**: 2026-07-07
**Type**: Animation (10-30s @ 60fps)

## Concept
A generative visualization of a recursive fractal tree that slowly sways and morphs as if blown by an invisible, organic wind. The structure branches recursively up to 13 generations, creating over 8000 distinct branch segments.

## Techniques
Uses a deeply recursive drawing function (`compute_tree`). Instead of generating drawing commands immediately within the recursion, it pre-computes the line segments and groups them by depth into lists (`lines_by_depth`). This allows py5 to render thousands of lines incredibly fast using batched `py5.begin_shape(py5.LINES)`. The angles of the branches are modulated continuously using overlapping `py5.os_noise` fields to simulate wind.

## Palette
Glowing autumn. A deep slate background. The thickest root branches glow in deep crimson/brown, gradually transitioning through fiery orange and gold, and finally culminating in bright yellow/white tips at the outermost leaves.

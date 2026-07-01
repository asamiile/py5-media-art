# Generative Isometric Labyrinth Growth 2D

## Concept
A procedural labyrinth maze that grows continuously via a Depth-First Search (DFS) space colonization algorithm, rendered from a 2D isometric perspective.

## Techniques
Uses standard 2D vector drawing to simulate a 3D isometric view. A DFS algorithm computes valid neighboring grid cells iteratively over multiple steps per frame to speed up growth. As the maze generates, the active "head" is highlighted with a glowing neon 3D block, while traversed paths leave behind thin cyan structural lines. A semi-transparent overlay provides slight motion trails.

## Format
Animation (29 seconds @ 60fps)

## Output
- `generative_isometric_labyrinth_growth_2d.mp4`
- `generative_isometric_labyrinth_growth_2d_p1.png`

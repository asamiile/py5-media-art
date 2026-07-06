# kinetic_optical_flow_glitch_grid_2d

**Date**: 2026-07-05
**Type**: Animation (10-30s @ 60fps)

## Concept
A high-contrast grid of symbols or simple shapes that glitch and shift rapidly, driven by an underlying optical flow algorithm running over invisible Perlin noise fields. It creates a feeling of a malfunctioning cybernetic matrix or a digital display under extreme electromagnetic interference.

## Techniques
A dense 2D grid structure. At each grid point, a simple glyph (like a square, line, or circle) is drawn. The size, rotation, and color are determined by the curl noise flow field at that point. We add random, high-frequency "glitch" offsets (sudden jumps in X/Y or color inversion) based on a secondary noise layer threshold to simulate digital tearing.

## Palette
Harsh cyberpunk contrast. Pitch black background, pure white base grid, with intense sudden flashes of pure magenta and cyan.

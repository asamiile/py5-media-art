# generative_isometric_optical_illusion_stairs_2d

**Date**: 2026-07-07
**Type**: Animation (10-30s @ 60fps)

## Concept
A continuously shifting, Escher-like infinite staircase built from isometric blocks. The structure slowly rises or falls, with blocks sliding into place from the void to form impossible geometries. The lighting angle slowly rotates around the scene, casting shifting shadows.

## Techniques
A 3D grid of blocks rendered using an isometric 2D projection. The height of each block is driven by a traveling sine wave combined with Perlin noise. The blocks are drawn back-to-front (depth sorted). Each face (top, left, right) is shaded dynamically based on a rotating light vector.

## Palette
Monochromatic architectural. Clean white and gray blocks with sharp, high-contrast shadows against a stark, pitch-black background.

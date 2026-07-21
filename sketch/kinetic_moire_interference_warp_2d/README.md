# kinetic_moire_interference_warp_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
A hypnotic optical illusion created by the interference of dense, rotating grid layers and expanding concentric circles. The resulting animation pulses and warps entirely through emergent geometric overlap rather than explicit animation.

## Techniques
Three very dense, high-frequency layers are drawn:
1. Concentric circles expanding outward from the center.
2. A dense grid of parallel lines rotating slowly clockwise.
3. Another dense grid of parallel lines rotating slowly counter-clockwise with a slight phase oscillation.

These are drawn using `py5.blend_mode(py5.DIFFERENCE)`. Because DIFFERENCE blending subtracts pixel values, the overlapping dense lines cancel each other out in mathematically perfect interference waves, generating immense Moiré patterns.

## Palette
Pure CMY (Cyan, Magenta, Yellow) lines on a pure black background.

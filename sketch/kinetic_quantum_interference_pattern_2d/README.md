# kinetic_quantum_interference_pattern_2d

**Date**: 2026-07-07
**Type**: Animation (10-30s @ 60fps)

## Concept
A visual representation of quantum wave interference. Multiple moving point sources emit concentric ripples. Where the ripples overlap, they create complex Moiré patterns and interference fringes. The sources orbit each other in chaotic patterns, causing the interference structure to shift and warp dramatically.

## Techniques
Uses a dense grid of pixels evaluated via numpy broadcasting for extreme performance. For each point, the intensity is calculated as the sum of sine waves based on the distance to multiple moving sources. The resulting value is mapped to a high-contrast color palette using a non-linear transfer function. Evaluated on a lower resolution off-screen buffer and scaled up.

## Palette
High contrast monochrome with iridescent highlights. Base is stark black and white, but the interference peaks are highlighted in iridescent cyan and magenta.

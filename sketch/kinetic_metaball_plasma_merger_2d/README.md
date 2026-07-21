# kinetic_metaball_plasma_merger_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
Fluid, glowing plasma globs (metaball-like structures) merging and splitting in a zero-gravity environment.

## Techniques
Instead of expensive raymarching, this achieves a 2D metaball/plasma effect by pre-rendering a large, very soft radial gradient brush with a cubic falloff. 80 particles wander around the screen using curl noise for fluid motion, pulling slightly towards the center. The particles are drawn using this brush with `py5.blend_mode(py5.ADD)`, causing overlapping regions to smoothly merge and ramp up in brightness.

## Palette
Neon greens and bright yellows, which additively blend into pure white in dense areas, set against a dark background that slowly fades.

# kinetic_ascii_fluid_terminal_glitch_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
A forgotten retro terminal system where the text itself begins to melt and flow like a liquid, eventually glitching into chaos.

## Techniques
Grid-based ASCII rendering with a global melt threshold driven by 2D Perlin noise. Cells below the threshold are advected downwards and their characters are sampled from noise, colored dynamically based on "velocity" (noise derivative approximation).

## Palette
Dark/Moody Retro-terminal. Phosphor green, dim green, and CRT bright cyan/magenta glitches on a dark background.

# generative_ascii_glitch_matrix_rain_2d

**Date**: 2026-07-07
**Type**: Animation (10-30s @ 60fps)

## Concept
A modern, glitch-art take on the classic "Matrix digital rain". Instead of just falling letters, it features glowing typographical glyphs that spawn, fall, and shatter into smaller particles upon hitting invisible obstacles. Periodically, waves of chromatic aberration sweep across the grid, shifting colors and characters randomly.

## Techniques
A grid system for the falling characters. An array stores the active "droplets" (x, y, speed, char). When a droplet falls, it leaves a fading trail in a secondary pixel buffer or using standard fade. The characters are drawn using `py5.text()`. Glitch effects are achieved by randomly offsetting the X and Y drawing coordinates for the red and blue color channels during the draw loop.

## Palette
Cyberpunk glitch. Base color is high-contrast matrix green on black, but chromatic aberration flashes introduce bright magenta and cyan splitting.

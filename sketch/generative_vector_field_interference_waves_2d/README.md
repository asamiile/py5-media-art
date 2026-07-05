# generative_vector_field_interference_waves_2d

**Date**: 2026-07-05
**Type**: Animation (10-30s @ 60fps)

## Concept
A visual exploration of multiple overlapping sinusoidal interference patterns mapped across a highly dense vector field. Millions of tiny line segments rotate dynamically in response to the constructive and destructive interference of the invisible waves passing through them.

## Techniques
Generates a grid of 60,000 tiny line segments. The angle of each segment is derived by summing 4 distinct rotating 2D sine waves with different frequencies and phases. Rendered natively with py5.LINES, utilizing numpy arrays to calculate all angles simultaneously and dynamically set the stroke color based on the local wave intensity.

## Palette
Electric neon interference. Deep black background with vivid, searing hues of magenta, neon green, and bright yellow.

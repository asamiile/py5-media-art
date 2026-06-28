# abstract_kinetic_topographical_interference_2d

**Date**: 2026-06-27

## Theme
A kinetic simulation of mathematical interference patterns that mimic overlapping topographical maps or moire rings. The patterns continually shift, align, and break apart.

## Technique
A fast, vectorized 2D grid of points using `numpy`. Complex sine and cosine interference equations are calculated over the grid, and only points above a certain interference threshold are drawn, resulting in pulsing contour lines and moire effects.

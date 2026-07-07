# kinetic_cellular_automata_belousov_zhabotinsky_2d

**Date**: 2026-07-07
**Type**: Animation (10-30s @ 60fps)

## Concept
A simulation of the Belousov-Zhabotinsky (BZ) reaction, an oscillating chemical reaction that creates mesmerizing spiral waves and expanding rings that annihilate upon collision.

## Techniques
Uses a cyclic multi-state cellular automaton on a dense grid of pixels. The simulation runs on a NumPy array, where cells transition through states based on the states of their Moore neighborhood. NumPy operations (`np.roll`, `np.where`) are used for highly efficient, vectorized grid updates, allowing the CA to run and be rendered as a scaled-up image via `py5.image()`.

## Palette
Fluorescent biological. Deep purple background with the expanding reaction waves glowing in radioactive cyan and electric yellow.

# generative_cellular_automata_bz_reaction_2d

- **Date**: 2026-07-04
- **Type**: Animation (900 frames, 60fps)

## Concept
A 16-state Cyclic Cellular Automaton simulating an excitable medium similar to a Belousov-Zhabotinsky (BZ) chemical reaction. The system rapidly organizes from initial noise blocks into beautifully intricate square spirals, labyrinthine waves, and glitch-matrix textures.

## Techniques
Computes the cellular automaton rules across an 8K High-DPI grid (over 33 million pixels) per frame. To bypass the extreme overhead of drawing shapes in python, `py5` rendering functions were entirely skipped. Instead, the grid state physics are evaluated using parallelized `numpy.roll` operations. The resulting states are mapped to a precomputed color array, which is then streamed instantly into `py5.np_pixels`. 
The specific choice of a threshold-1 Moore neighborhood forces the waves to expand in orthogonal and diagonal bounds, yielding sharp square "Aztec" spirals instead of traditional circular BZ waves.

## Palette
Highly saturated, iridescent neon color cycle that shifts smoothly across the 16 states.

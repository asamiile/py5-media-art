# kinetic_cellular_automata_game_of_life_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
A cinematic, cybernetic reimagining of Conway's classic "Game of Life" cellular automaton. Instead of rigid pixels flashing on and off, this artwork treats the grid as a living neural network or a high-tech circuit board. Cells smoothly bloom into existence and fade away, leaving glowing trails and connecting lines to their neighbors.

## Techniques
- **Cellular Automata**: The simulation runs the standard Conway rules (survival with 2 or 3 neighbors, birth with exactly 3 neighbors) evaluated natively via NumPy slicing for speed.
- **Temporal Smoothing**: A secondary `smooth_state` matrix interpolates towards the logical `state` each frame. This transforms the harsh binary flips of the automata into smooth, organic breathing motions.
- **Connected Graph Visuals**: If adjacent cells are both highly active, a faint line connects them, emphasizing the structure of the "gliders" and "oscillators" that emerge.
- **Noise-Driven Palette**: The color of each active cell shifts smoothly between cyan and magenta based on 3D OpenSimplex noise mapped to its coordinate and time.

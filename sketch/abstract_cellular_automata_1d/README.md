# abstract_cellular_automata_1d

A 3D simulation of a 1-dimensional Cellular Automaton (Rule 30) woven into a dynamic physical fabric.

- **Date**: 2026-05-23
- **Theme**: Cellular Automata, Rule 30, Stephen Wolfram, computational irreducibility, digital fabric, weaving.
- **Technique**: First, a 1D Cellular Automaton (Rule 30) is calculated for 150 generations across a grid of 120 cells using a classic bitwise evaluation loop. Instead of rendering this as a flat 2D pixel grid, the space-time history (where Y is time and X is the cell index) is mapped onto the surface of a 3D cylinder using polar coordinates (`py5.QUADS`). To make it kinetic, a time-based 3D Perlin noise field deforms the radius of the cylinder continuously. The result is a mathematically complex, non-repeating triangular fractal pattern that appears to be woven into a piece of digital fabric flapping in a simulated wind. 15s 60fps MP4.
- **Description**: A massive, woven tube of glowing fabric floats in the dark. The fabric is patterned with the iconic, chaotic triangles of Cellular Automaton Rule 30—the same mathematical pattern found on the shells of Conus textile snails. As the tube slowly rotates, an invisible wind causes the digital cloth to ripple and warp. The "living" cells (1s) glow in shifting neon hues, while the "dead" cells (0s) form a dark, semi-transparent mesh, blending rigid computer science with organic, flowing textiles.

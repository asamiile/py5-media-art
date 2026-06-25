# Generative Kinetic Cellular Automata

An animated 15s sequence of cyclic cellular automata producing spiral waves.

## Concept

- **Theme**: A continuous 2D cellular automata generating hypnotic, propagating wave patterns reminiscent of chemical oscillations or biological growth.
- **Technique**: Cyclic Cellular Automata on a 2D grid. Cells sequentially adopt the state of their neighbors if the neighbor is exactly one state ahead. Evaluated rapidly using vectorized NumPy operations and rendered as dense quads in Py5.
- **Palette**: A full psychedelic spectrum where grid states map to hues that continuously shift over time.

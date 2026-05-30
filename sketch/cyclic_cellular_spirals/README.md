# cyclic_cellular_spirals

A generative digital media art animation depicting expanding, self-organizing geometric spirals in a multi-state cyclic cellular automaton.

## Artistic Theme

This work evokes the rhythmic ripples of chemical crystallization (like the Belousov-Zhabotinsky reaction) and thermodynamic self-organization in active media. The canvas starts with isolated seed nodes that rapidly expand outward, creating concentric color waves. As these wavefronts meet, they form sharp, swirling spiral junctions that rotate and shear against one another. The color transitions smoothly through a cyclic Stop palette (Indigo -> Teal -> Gold -> Magenta), presenting a continuously changing kaleidoscope of geometric order emerging out of local interaction rules.

## Technique

- **Cyclic CA Simulation**: Evolves on a $480 \times 270$ grid scaled up to $3840 \times 2160$ for output. Cells take states $s \in [0, 15]$. A cell transitions from state $s$ to $(s + 1) \pmod{16}$ if it has at least 2 neighbors in that target state.
- **Vectorized Update & Rendering**: Shift checks are vectorized in NumPy using `np.roll` for periodic boundary conditions, achieving over 60fps simulation speeds. The cell states are mapped to HSB interpolated RGB colors, multiplied by a cinematic vignette mask, and written directly to a py5 image buffer for high-performance scale rendering.
- **Composition & Video**: Compiled at 4K resolution at 60fps with a 10-second duration.

## Running

Run the animation and compile the MP4 video using the `uv` toolchain:

```bash
uv run python sketch/cyclic_cellular_spirals/main.py
```

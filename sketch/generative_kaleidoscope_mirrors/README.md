# generative_kaleidoscope_mirrors

A hypnotic, procedurally generated 12-axis optical kaleidoscope.

- **Date**: 2026-05-23
- **Theme**: Optical illusions, kaleidoscope, perfect symmetry, generative curves.
- **Technique**: Demonstrates the mathematical power of matrix transformations (`py5.push_matrix`, `py5.rotate`, `py5.scale`). A highly complex, chaotic, and asymmetrical base segment consisting of twisting, noise-driven 3D bezier curves is calculated and drawn inside a single wedge (1/12th of a circle). This base wedge is then copied, rotated, and mirrored (`scale(1, -1)`) 12 times in a loop. Because the base geometry relies on Perlin noise driven by time, the chaos morphs organically, but the matrix mirroring forces it into absolute, mesmerizing, radial symmetry. 15s 60fps MP4.
- **Description**: Symmetrical ribbons of glowing neon light twist, fold, and bloom like an alien flower inside a massive kaleidoscope. The shapes are chaotic, forming sharp angles and elegant loops, but they are perfectly mirrored across 12 axes. As the entire mandala slowly rotates, the internal geometry breathes and shifts, creating a flawless, deeply satisfying optical illusion of perfect fractal symmetry out of pure random noise.

# kinetic_math_clifford_attractor_morph_2d

- **Date**: 2026-07-05
- **Type**: Animation (536 frames, 60fps)

## Concept
A Peter de Jong Strange Attractor that breathes, shifts, and folds infinitely as its underlying four mathematical parameters are continuously modulated by a 2D Perlin noise field. The attractor morphs between different beautifully intricate chaotic regimes.

## Techniques
Instead of using standard particle drawing routines which would crash the JVM with millions of vertices, this sketch uses a highly optimized pure-Python data processing approach.
In each frame, 1 million "particles" are warmed up for 40 iterations until they cleanly settle onto the attractor's manifold. Then, they are traced for another 30 iterations, generating 30 million data points per frame.
These points are binned into a massive Numpy 2D histogram matrix (an 8K density map). The hit counts are scaled logarithmically to achieve an incredible dynamic range, converting raw math directly into an iridescent, glowing, incredibly detailed fractal rendering which is then streamed directly to `py5.np_pixels`.

## Palette
A rich, shifting neon gradient. Dark blue and violet represent the wispy low-density edges, shifting cleanly through hot pink into electric cyan and pure white at the core highest-density structural paths of the attractor.

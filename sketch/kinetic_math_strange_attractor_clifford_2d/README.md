# kinetic_math_strange_attractor_clifford_2d

A visualization of the Clifford strange attractor continuously morphing its defining parameters over time. 300,000 independent particles trace out the attractor's complex, folding fractal structure.

## Techniques

Highly optimized NumPy vectorization iterating the Clifford map equations for 300,000 points simultaneously. The points are drawn with very low opacity to build up a density map, creating ghostly, smooth motion blur.

## Palette

Monochromatic-adjacent glowing structure that shifts gradually from cyan to magenta, built up through additive blending on a deep dark background.

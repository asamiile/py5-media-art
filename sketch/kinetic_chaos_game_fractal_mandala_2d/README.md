# Kinetic Chaos Game Fractal Mandala 2D

## Concept
A mesmerizing, morphing fractal generated using the Chaos Game algorithm (Iterated Function Systems). Thousands of glowing particles jump towards dynamic attractor points arranged in a hexagonal mandala shape, slowly revealing a glowing, incredibly intricate fractal geometry that breathes as the attractors rotate.

## Technical Implementation
- Simulates a classic Chaos Game on a hexagon with 6 dynamically shifting attractor vertices.
- The 6 vertices slowly pulse in and out radially and rotate over time, creating a breathing motion.
- 300,000 persistent points jump halfway towards a randomly chosen vertex 5 times per frame at 60fps.
- Vectorized numpy arrays handle the jumping math and color interpolation concurrently.
- Points are rendered as tiny additive dots using `py5.points`, grouped by their target vertex color to accumulate a continuous Sierpinski-like fractal mandala.

## Execution
- `Particles`: 300,000 persistent points
- `FPS`: 60
- `Duration`: 15 Seconds
- `Resolution`: 3840x2160

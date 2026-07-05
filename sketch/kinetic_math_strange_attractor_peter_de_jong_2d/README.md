# kinetic_math_strange_attractor_peter_de_jong_2d

A visualization of the Peter de Jong strange attractor, an iterative chaotic map. Over time, the parameters of the equations slowly drift, causing the attractor's shape to continuously fold, unfold, and evolve into new intricate fractal patterns.

## Techniques

Computes 500,000 points per frame using vectorized NumPy arrays by simulating 10,000 independent parallel trajectories. Renders the massive point cloud using additive blending and a slight motion blur trail.

## Palette

"Stellar Dust": Bright, glowing golden and orange points scattered across a deep midnight blue background, giving the appearance of cosmic dust or a glowing nebula.

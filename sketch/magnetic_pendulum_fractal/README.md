# magnetic_pendulum_fractal

The mesmerizing fractal boundaries of a magnetic pendulum's phase space.

- **Date**: 2026-05-23
- **Theme**: Physics simulation, fractals, chaos theory, basins of attraction.
- **Technique**: Instead of simulating a single pendulum swinging between three magnets, we treat the entire canvas as a grid of 500,000 different starting positions $(X, Y)$ and simulate them all simultaneously using vectorized NumPy operations. Over the course of the 15-second animation, the positions of all pendulums are integrated using Euler's method. The color of each pixel corresponds to the proximity of its respective pendulum to the three magnets (Red, Green, Blue). As the pendulums fall into the gravitational and magnetic wells, the smooth color fields shatter into infinitely complex fractal boundaries. 15s 60fps MP4.
- **Description**: What begins as a smooth, blurry RGB gradient slowly warps and folds as the invisible pendulums start swinging. Gravity and magnetism violently pull the system apart, revealing a stunning, razor-sharp fractal crystal where tiny changes in starting position determine which magnet a pendulum ultimately lands on.

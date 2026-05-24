# abstract_generative_strange_attractor_lorenz

A highly chaotic, mathematical 3D visualization of the Lorenz Strange Attractor.

- **Date**: 2026-05-23
- **Theme**: Chaos theory, strange attractors, the butterfly effect, fluid convection, math.
- **Technique**: Solves the Lorenz system of nonlinear ordinary differential equations ($\frac{dx}{dt} = \sigma(y - x)$, $\frac{dy}{dt} = x(\rho - z) - y$, $\frac{dz}{dt} = xy - \beta z$) for 15,000 independent particles simultaneously. The entire swarm is initialized in a microscopic cluster of a $0.01$ radius. Due to the chaotic nature of the strange attractor (the "Butterfly Effect"), infinitesimally small initial differences cause the particles' paths to rapidly diverge. The physics are computed using vectorized NumPy operations for high performance. The particles are drawn as a continuous, fading neon ribbon (`py5.line` with additive blending and motion blur) that reveals the iconic dual-lobe "butterfly" shape of the attractor over time. 15s 60fps MP4.
- **Description**: The Butterfly Effect made visible. 15,000 points of light begin as a single microscopic drop, but within seconds, the laws of chaos rip them apart. They spiral outward, tracing the invisible mathematical currents of the Lorenz Strange Attractor. The paths weave a massive, glowing, two-lobed structure that looks like cosmic gossamer wings. The camera slowly orbits the 3D structure, showing the intricate, non-intersecting layers of infinite complexity drawn in deep purples and electric pinks.

# superfluid_tangle

A simulation of quantum vortex dynamics in a frictionless superfluid, visualized through the chaotic motion of tracer particles.

## Concept
This work explores the emergence of complex "tangles" in superfluids at near-absolute zero temperatures. It models the velocity field induced by discrete vortex filaments (point vortices in 2D) and shows how tracer particles are captured and spun around these frictionless singularities.

## Technique
- **Biot-Savart Law**: Calculates the 2D velocity field $v(z) = \sum \frac{i \Gamma_i}{2\pi (\bar{z} - \bar{z}_i)}$ where $\Gamma_i$ is the vortex strength.
- **Quantum Tangle**: Vortex positions are perturbed by high-frequency Perlin noise to simulate the jitter and reconnection events typical of quantum turbulence.
- **Spectral Velocity Mapping**: 3,000 tracer particles are colored on a HSB gradient from Cyan (low velocity) to Violet (high velocity), creating a heat-map of the fluid's kinetic energy.
- **Additive Synthesis**: 30-frame history buffers are rendered with `SCREEN` blending to create glowing, continuous filaments.

## Files
- `main.py`: The simulation and rendering engine.
- `output.mp4`: The 5-second 60fps animation.
- `preview.png`: A high-detail snapshot of the turbulent flow.

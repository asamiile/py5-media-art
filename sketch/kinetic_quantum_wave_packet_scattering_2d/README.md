# kinetic_quantum_wave_packet_scattering_2d

An animated 2D quantum mechanical simulation solving the Time-Dependent Schrödinger Equation (TDSE) to visualize wave packet scattering, double-slit diffraction, and obstacle reflection.

## Concept & Visuals
The simulation solves the 2D Schrödinger equation using a symplectic finite-difference time-domain (FDTD) leapfrog method:
- **Probability Density** ($|\psi|^2$) determines brightness/glowing intensity.
- **Complex Phase** ($\text{arg}(\psi)$) determines color mapping (hue) using an iridescent spectral color wheel.
- As the wave packet hits the barrier, it splits, diffracts, and interferes, creating complex standing waves and circular ripples.
- Absorbing sponge boundaries damp the wave amplitude smoothly at the edges, preventing artificial reflections.

## Technical Implementation
- Vectorized 2D NumPy Laplacian updates running 8 sub-steps per frame for high numerical stability.
- Custom potential barrier mask representing a double-slit aperture and multiple circular obstacles.
- Blending simulation visualization with native 4K vector HUD telemetry showing simulator diagnostics.

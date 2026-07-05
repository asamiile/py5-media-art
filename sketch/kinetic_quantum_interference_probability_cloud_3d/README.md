# kinetic_quantum_interference_probability_cloud_3d

Simulating the probability density of an electron orbital (like the Hydrogen atom 4f orbital) using half a million points, slowly rotating the orbital in 3D space.

## Techniques

Evaluates a spherical harmonic function combined with a radial distribution over 500,000 points. 3D coordinates are mapped to the probability density function, filtering out points below a probability threshold, and rendered with additive blending while rotating the camera.

## Palette

Deep space background. The probability lobes are rendered in glowing cyan and magenta, representing positive and negative phase.

# prismatic_reflection

A visualization of light's recursive journey through a dark geometric labyrinth, fracturing into spectral components with every encounter.

## Concept
This work simulates the physical phenomenon of prismatic dispersion within an infinite hall of mirrors. It explores how a single source of white light can become a complex, layered tapestry of color when subjected to recursive reflection and wavelength-dependent refraction indices.

## Technique
- **Recursive Ray-Casting**: 2D ray-segment intersection logic with a maximum bounce depth of 20.
- **Spectral Decomposition**: Light is modeled as 15 discrete wavelength channels, each with a slightly different starting angle and cumulative dispersion shift.
- **Mirror Maze**: A 12-sided polygon boundary with an internal star-pattern mirror lattice created using non-adjacent vertex connections.
- **Additive Synthesis**: Ray segments are rendered using `ADD` blending with extremely low alpha (0.04) to simulate the buildup of light intensity and spectral fringes.

## Files
- `main.py`: The simulation and rendering logic.
- `preview.png`: The resulting high-resolution prismatic visualization.

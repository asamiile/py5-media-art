# kinetic_cellular_automata_lenia_2d

A continuous cellular automata simulation based on the Lenia framework, manifesting complex, organic, alien-like lifeforms.

## Technical Details
- **Resolution**: 4K (3840x2160) (Simulated at 1920x1080, upscaled for rendering)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
While traditional cellular automata like Conway's Game of Life use discrete grids and binary states, Lenia is entirely continuous in space, time, and state. 
This sketch implements Lenia using Fast Fourier Transforms (FFT) in NumPy to efficiently compute 2D convolutions with a bell-shaped ring kernel. The resulting neighborhood field is passed through a Gaussian growth function to advance the continuous Euler integration.
Starting from a small patch of random noise, self-organizing "organisms" rapidly emerge, swimming, rotating, and dividing organically across the canvas. The continuous scalar field is mapped to a bioluminescent green-teal gradient, presenting the digital ecosystem like microorganisms under a neon microscope.

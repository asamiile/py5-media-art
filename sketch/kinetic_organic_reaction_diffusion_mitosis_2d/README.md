# kinetic_organic_reaction_diffusion_mitosis_2d

An algorithmic visualization of the Gray-Scott Reaction-Diffusion model, simulating organic cellular growth and morphological phase transitions.

## Technical Details
- **Resolution**: 4K (3840x2160) (Simulated at 1920x1080, upscaled for rendering)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
This sketch simulates the interaction of two hypothetical chemicals ($A$ and $B$) diffusing and reacting on a 2D grid. The continuous PDEs are solved using Euler integration and a highly optimized 3x3 Laplacian convolution implemented via `NumPy`'s `roll` operation, allowing the simulation to advance 15 time-steps per frame across 2 million grid cells.
To make the animation kinetic and evolutionary, the feed rate ($f$) and kill rate ($k$) are linearly interpolated over the 15-second duration. The system begins in a "Mitosis" parameter state, resulting in dividing cellular blobs, and slowly transitions into a "Coral/Maze" parameter state, forming intricate interlocking ridges. The concentration of chemical $B$ is color-mapped into a gradient from midnight blue to vibrant magenta and glowing gold.

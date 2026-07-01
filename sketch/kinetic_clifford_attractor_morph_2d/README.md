# kinetic_clifford_attractor_morph_2d

An animated generative sequence exploring the Clifford Attractor, a discrete 2D chaotic map known for producing beautifully intricate, smoky, and veil-like interference patterns.

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
The animation utilizes NumPy to simultaneously compute the trajectories of 500,000 independent points mapping through the Clifford equations:
$X_{n+1} = \sin(a Y_n) + c \cos(a X_n)$
$Y_{n+1} = \sin(b X_n) + d \cos(b Y_n)$

To create kinetic morphing, the four core parameters ($a, b, c, d$) are driven by slow sinusoidal time-offsets, forcing the attractor to bend, stretch, and reorganise its phase space dynamically. The dense point cloud is rendered using very low-opacity additive blending `py5.POINTS` against a motion-blurred canvas, allowing the recursive geometry to build up as glowing veils of light. Particles are colored into Cyan, Magenta, and Gold gradients based on their spatial positions, enhancing depth and structure.

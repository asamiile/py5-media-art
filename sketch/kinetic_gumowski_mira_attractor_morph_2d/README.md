# kinetic_gumowski_mira_attractor_morph_2d

An abstract visualization of the Gumowski-Mira attractor, a discrete 2D chaotic mapping that yields highly organic, alien-like geometries reminiscent of marine life or microscopic biological structures.

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
The animation utilizes NumPy to simultaneously compute the phase-space trajectories of 300,000 independent particles. The mathematical rules for the Gumowski-Mira map evaluate sequentially ($X_{n+1}$ depends on $Y_n$ and $X_n$, and $Y_{n+1}$ depends on $X_{n+1}$). To give the structure life, the non-linear transformation parameter $a$ is continuously modulated via a sine wave, forcing the geometry to dynamically breathe, expand, and fold in on itself.
The particles are binned into three boolean masks based on their polar angle relative to the origin, which applies a radial gradient (Red/Orange, Cyan/Blue, Purple/Magenta). These points are rendered with a very low-opacity additive blend (`py5.POINTS`) against a dark purple background, leaving smoky, volumetric trails that emphasize the dense phase-space boundaries.

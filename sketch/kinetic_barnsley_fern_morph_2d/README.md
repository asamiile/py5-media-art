# kinetic_barnsley_fern_morph_2d

An animated sequence demonstrating an Iterated Function System (IFS) morphing organically. The classic Barnsley Fern fractal is continuously manipulated by slowly shifting its affine transformation matrix coefficients using trigonometric noise over time, making it breathe, sway, and organically curl.

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
Rather than generating the fractal point-by-point, a dense array of 300,000 NumPy particles are simultaneously mapped through the IFS. Each frame, four iterations are applied using boolean masks representing the cumulative probabilities of the 4 standard transformation matrices. The transformation coefficients $b, c$ are modulated with time, simulating a wind that organically curls the leaflets. 
The rendering highlights the recursive nature by assigning unique, vibrant neon colors to the particles based on which of the four affine transformations was most recently applied to them. Rendered using `py5.POINTS` and additive blending.

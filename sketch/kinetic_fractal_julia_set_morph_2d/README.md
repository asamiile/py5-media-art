# kinetic_fractal_julia_set_morph_2d

A mesmerizing generative animation diving into the mathematics of the Julia Set ($z_{n+1} = z_n^2 + c$).

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
This sketch evaluates the Julia set equation for all 8.2 million pixels on the 4K canvas simultaneously using highly optimized NumPy array operations. By smoothly moving the complex parameter $c$ along a circular path in the complex plane (with a slight sinusoidal radial wobble), the fractal geometry continuously morphs, unfolding into intricate dragon-like patterns and spiraling tendrils.
A continuous potential algorithm (smooth iteration count) is used to eliminate color banding, allowing the escape times to be mapped precisely into a continuous trigonometric color palette. The palette shifts gracefully between deep purples, neon cyans, and magentas, contrasting sharply with the pitch-black interior of the fractal set.

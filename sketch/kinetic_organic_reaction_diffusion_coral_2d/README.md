# kinetic_organic_reaction_diffusion_coral_2d

A simulation of the Gray-Scott reaction-diffusion model, creating organic, coral-like structures that slowly grow, pulse, and shift across the screen.

## Techniques

Numerically integrates the reaction-diffusion partial differential equations using heavily vectorized NumPy operations (`np.roll`) on a lower-resolution grid for high performance. The parameters dynamically oscillate, causing the growth patterns to breathe and morph over time. The chemical concentrations are directly mapped to pixel colors using `img.np_pixels`.

## Palette

A deep ocean teal background contrasting with bright, glowing coral pink and orange cellular structures.

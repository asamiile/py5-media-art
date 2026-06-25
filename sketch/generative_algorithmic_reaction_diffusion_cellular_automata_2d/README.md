# generative_algorithmic_reaction_diffusion_cellular_automata_2d

An animated 15s sequence of generative algorithmic reaction diffusion cellular automata in 2D.

## Concept

A continuous cellular automata simulating reaction-diffusion, creating intricate zebra stripes and fingerprint-like patterns that evolve and merge smoothly, glowing in vibrant colors.

## Technique

A numerical approximation of the Gray-Scott reaction-diffusion model. The simulation runs on a downscaled grid for performance, using numpy for vectorized calculations. The resulting concentration values are mapped to shifting, psychedelic RGB colors and drawn as small rectangles.

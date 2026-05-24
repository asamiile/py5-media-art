# generative_vector_field_perlin_flow

A fluid dynamics visualization simulating 30,000 glowing particles swept through a mutating Perlin noise vector field.

- **Date**: 2026-05-23
- **Theme**: Fluid dynamics, vector fields, Perlin noise, wind currents, Van Gogh's Starry Night, organic flow.
- **Technique**: Uses NumPy arrays to manage the positions and velocities of 30,000 individual particles. In every frame, a 3D Perlin noise function evaluates the precise angle of a "wind current" at each particle's exact (x, y) location. The third dimension of the noise function is bound to time, causing the entire invisible vector field to slowly mutate and boil. The background is not completely cleared between frames; instead, a highly transparent black rectangle is drawn over the canvas, causing the moving particles to leave long, fading trails (`py5.background` motion blur effect). The particles are colored based on their current angle of travel. 15s 60fps MP4.
- **Description**: Like a digital painting of a cosmic wind storm. 30,000 glowing neon dust particles flow across the screen, caught in an invisible, churning atmospheric current. They weave into intricate, interlocking spirals, whirlpools, and flowing rivers of light that resemble the swirling skies of Van Gogh's *Starry Night* or the intricate rings of polished wood grain. As the underlying wind field slowly shifts, the entire glowing tapestry continuously repaints itself in waves of shifting cyan, magenta, and gold.

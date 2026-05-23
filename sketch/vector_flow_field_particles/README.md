# vector_flow_field_particles

Half a million glowing particles tracing the hidden contours of an analytical vector flow field.

- **Date**: 2026-05-23
- **Theme**: Fluid dynamics, vector fields, particle trails, generative art.
- **Technique**: To maintain 60fps while simulating 500,000 particles, we bypass computationally heavy Perlin noise and instead generate a smooth pseudo-random flow field using a combination of multiple low-frequency sine and cosine waves. This creates continuous, chaotic eddies and currents. The particles update their positions based on this vector field every frame. The background is only faintly cleared (10/255 opacity) each frame, allowing the particles to leave extremely long, smooth light trails. Rendered via additive blending directly into the `py5.np_pixels` buffer. 15s 60fps MP4.
- **Description**: Millions of bright cyan, blue, and white strands flow across the dark canvas like glowing silk threads caught in an invisible river. They converge into massive, swirling vortexes and split along unseen ridges. As the invisible math underlying the currents slowly shifts over time, the beautiful, complex structures elegantly unspool and reform into new shapes.

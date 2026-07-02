# generative_reaction_diffusion_turing_patterns_2d

An animated sequence of generative reaction diffusion turing patterns in 2D.

- **Theme**: A mesmerizing visual simulation of Turing patterns using the Gray-Scott reaction-diffusion model. The system continuously evolves, simulating the chemical reactions that form animal coats, coral structures, and cellular membranes.
- **Technique**: High-performance 2D cellular automaton in NumPy using the Gray-Scott equations. Spatial convolution (the Laplacian) is computed using rapid array shifting (`np.roll`). The simulation runs on a lower resolution grid (960x540) for performance, taking multiple sub-steps per frame, and is scaled up using bi-linear interpolation to 4K. The chemical concentration is mapped to a striking neon bioluminescent colormap.
- **Format**: Animation (15s @ 60fps)

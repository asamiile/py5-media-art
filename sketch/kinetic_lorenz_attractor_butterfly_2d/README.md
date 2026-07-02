# kinetic_lorenz_attractor_butterfly_2d

An animated sequence of kinetic lorenz attractor butterfly in 2D.

- **Theme**: A mesmerizing visualization of chaos theory. 50,000 autonomous particles trace the 3D Lorenz Attractor, their paths projected onto a 2D plane. Starting from a tightly packed cluster, the particles rapidly diverge, mapping out the iconic "butterfly" manifold in continuous motion, leaving ethereal, glowing trails.
- **Technique**: High-performance Ordinary Differential Equation (ODE) integration using NumPy. The system uses the Euler method to step 50,000 particles through the Lorenz vector field. The 3D coordinates are projected into 2D using a subtle isometric rotation. Particles leave semi-transparent trails using additive blending, colored continuously via their depth (Z-coordinate) into 10 depth bins.
- **Format**: Animation (15s @ 60fps)

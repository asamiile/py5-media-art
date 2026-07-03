# kinetic_vasarely_op_art_lattice_2d

An animated sequence of kinetic vasarely op art lattice in 2D.

- **Theme**: A homage to Victor Vasarely and the Op-Art movement. A dense lattice of geometric primitives (spheres) forms a continuous, undulating optical illusion. The size and color of each element shift based on a slow-moving, multi-dimensional noise field, creating the perception of a breathing 3D topological surface on a 2D plane.
- **Technique**: 2D geometric grid rendering. A hexagonal lattice is generated mathematically. The radius and color of each lattice node are driven by `py5.os_noise()`, mapping a low-frequency 3D noise space to size and a curated color palette. Pure vector shapes (`py5.ellipse`) scale infinitely well.
- **Format**: Animation (15s @ 60fps)

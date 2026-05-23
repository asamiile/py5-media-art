# geometric_fractal_polyhedron_subdivision

A breathing 3D fractal jewel generated through recursive polyhedron subdivision.

- **Date**: 2026-05-23
- **Theme**: Sacred geometry, recursive subdivision, platonic solids, geodesic domes, fractal breathing.
- **Technique**: The script begins with a mathematically perfect Icosahedron (a 20-sided Platonic solid derived from the Golden Ratio). Before drawing, it performs 4 levels of recursive subdivision on the CPU, splitting each triangular face into 4 smaller triangles and projecting the new vertices back onto a unit sphere, creating a dense geodesic mesh (thousands of triangles). During the draw loop, the position of every single vertex is displaced outward or inward based on a 3D volumetric sine wave interference pattern. This displacement causes the rigid geometry to "breathe" and warp dynamically. The faces are rendered semi-transparent with glowing edges (`py5.TRIANGLES`). 15s 60fps MP4.
- **Description**: A gigantic, glowing geodesic crystal floats and rotates slowly in a void. What starts as a perfect sphere made of thousands of tiny triangular glass panels suddenly begins to warp and breathe. Three-dimensional ripples travel across its surface, pulling the sharp vertices outward into spiked fractal crowns and pushing them inward to form deep craters. The facets gleam in shifting colors of cyan, magenta, and gold as the simulated light hits the continuously rippling, breathing digital crystal.

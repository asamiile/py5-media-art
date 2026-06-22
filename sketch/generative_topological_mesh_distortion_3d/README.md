# generative_topological_mesh_distortion_3d

An animated 15s sequence of a high-contrast, glowing 3D mesh that distorts continuously, creating mountain-like peaks and valleys that roll across the surface like waves.

- **Theme**: A high-contrast, glowing 3D mesh that distorts continuously, creating mountain-like peaks and valleys that roll across the surface like waves.
- **Technique**: Generates a grid of vertices in 3D. It uses 2D perlin noise mapped to the Z-axis, driven by time so the noise moves across the grid over time. Using `py5.TRIANGLE_STRIP`, it renders the surface as a wireframe.

![Preview](generative_topological_mesh_distortion_3d_p1.png)

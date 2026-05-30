# cybernetic_grid_displacement_3d

- **Date**: 2026-05-28
- **Theme**: A rigid 3D grid of lines that displaces dramatically based on a wandering 3D Perlin noise field, creating a digital landscape that undulates like a cybernetic ocean.
- **Technique**: Create a 2D array of grid points in the X-Z plane. Loop through the grid points and modify their Y-coordinates based on `py5.os_noise()` (OpenSimplex noise) with time and spatial coordinates as inputs. Draw the grid by connecting adjacent points with lines in P3D space.
- **Description**: An animated 3D grid landscape displaced by Perlin noise.

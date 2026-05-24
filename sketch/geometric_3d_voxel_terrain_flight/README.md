# geometric_3d_voxel_terrain_flight

A retro-futuristic 3D flight simulation over an infinite procedurally generated voxel landscape.

- **Date**: 2026-05-23
- **Theme**: Voxel engines, flight simulation, procedural terrain, retro 3D, topographic mapping.
- **Technique**: Uses a 2D Perlin noise map to generate a continuously scrolling 3D terrain grid. Rather than rendering the terrain as a smooth mesh, it is rendered discretely using 1,800 individual 3D cubes (`py5.box`), creating a retro voxel aesthetic similar to Minecraft or early 3D renders. The `y`-axis of the Perlin noise input is continuously decremented, creating the illusion of endless forward flight. A dynamic `py5.camera()` controls the viewport, banking left, right, up, and down as it flies through the valleys. The cubes are colored topographically based on their height, with the highest peaks assigned `py5.emissive()` materials so they glow like volcanic lava or neon snow in the dark atmosphere. 15s 60fps MP4.
- **Description**: The camera hurtles forward through a digital canyon made entirely of floating geometric cubes. Below, a jagged, blocky terrain of deep purple valleys and towering magenta peaks scrolls by endlessly. The camera smoothly banks and bobs as if mounted to a flying drone. As the drone passes over the tallest mountain ranges, the tips of the voxel towers glow with a blinding, emissive heat, illuminating the atmospheric fog of the digital world.

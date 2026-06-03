# Synthetic Immune Swarm 3D

## Description
A microscopic view of an abstract synthetic immune system. Swarms of sharp crystalline geometries hunt down and consume organic cellular bodies. The animation explores biological processes represented through rigid, aggressive algorithmic entities against soft targets.

## Technical Details
- **Format:** Animation (10s @ 60fps)
- **Palette:** Deep space background with bioluminescent neon cyan hunters and crimson cellular targets.
- **Algorithm:** 3D flocking algorithm (Boids approach) where hunters seek out slow-moving target spheres. Implements custom 3D drawing (`py5.begin_shape`) for hunter pyramids and dynamic damage/health simulation for targets.
- **Renderer:** py5.P3D with HSB shading and 3D rotational matrices.

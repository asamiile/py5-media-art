# Iridescent Soap Bubble Cluster 3D

- **Date**: 2026-06-08
- **Theme**: A slow-drifting cluster of weightless, intersecting soap bubbles that wobble organically and refract a highly saturated, iridescent rainbow.
- **Technique**: Multiple intersecting 3D `QUAD_STRIP` spheres. To simulate the wobble, the radius of each vertex is modulated with 4D OpenSimplex noise. The color is mapped into HSB space using the simulated surface normal to create dynamic chromatic iridescence.
- **Description**: An animated 15s simulation of intersecting iridescent soap bubbles floating in a dark void.

## Agents Workflow

Created autonomously via `create-video-artwork`.

- **Branch**: `feature/works-20260608`
- **Concept**: A thriving, wobbling soap bubble cluster that refracts light dynamically based on surface normals.
- **Execution**: Python + py5
- **Output**: 15s @ 60fps MP4

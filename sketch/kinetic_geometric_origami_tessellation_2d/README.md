# kinetic_geometric_origami_tessellation_2d

**Date**: 2026-07-07
**Type**: Animation (10-30s @ 60fps)

## Concept
A plane of interlocking triangles (like an origami tessellation) that continuously folds and unfolds rhythmically. As "waves" of folding energy pass through the plane, the triangles rotate and cast dynamic shadows, creating a breathing, living geometric surface.

## Techniques
A hexagonal/triangular grid of vertices. We apply a 2D traveling sine wave combined with Perlin noise to modulate the 3D position of each vertex. The triangles are drawn with a simple simulated directional light (Lambertian shading) to enhance the 3D folding effect. Vertex positions are projected back to 2D screen space to render the pseudo-3D scene.

## Palette
Pastel minimalism. Soft peach, mint green, and pale lavender triangles on a pristine white background. Shadows are dynamic based on the simulated directional light.

# kinetic_fluid_vector_field_flow_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
A glowing, fluid simulation of 15,000 particles sweeping through a massively turbulent, mathematically generated vector field. The result looks like shimmering silk or luminescent ocean currents in a dark abyss.

## Techniques
- **Vectorized Trigonometric Field**: Instead of relying on expensive Perlin noise lookups in Python, the underlying vector field is constructed from layers of intersecting `sin` and `cos` waves evaluated instantaneously over all particles using NumPy.
- **Dynamic Vortices**: A large vortex constraint is applied to the center of the field, whose polarity slowly oscillates over time, pulling and pushing the particles in vast spiraling patterns.
- **Additive Trail Blending**: As particles traverse the field, a faint black rectangle (alpha 15) is drawn each frame instead of a full clear. Combined with `py5.blend_mode(py5.ADD)`, this creates long, overlapping ribbons of light.

## Palette
Deep oceanic blues and teals that transition to intense, white-hot highlights where particles clump densely.

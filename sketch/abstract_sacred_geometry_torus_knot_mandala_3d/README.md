# abstract_sacred_geometry_torus_knot_mandala_3d

An animated 20s sequence of multiple intertwined 3D Torus Knots that rotate and interlock, creating a glowing wireframe mandala.

## Theme
A 3D hyperbolic geometry tessellation projected onto multiple interlocking Torus Knots, slowly rotating and breathing.

## Technique
Five complex Torus Knots (`p=3, q=7`) are drawn using `py5.begin_shape(py5.LINE_STRIP)`. Each knot is rotated symmetrically to form a star-like 3D mandala. The geometry is distorted by `py5.os_noise` based on its position and time, giving it an organic, breathing quality. The entire structure rotates in 3D space with a glowing neon hue mapped to the drawing index and time. Additive blending (`py5.ADD`) emphasizes the interlocking density at the center.

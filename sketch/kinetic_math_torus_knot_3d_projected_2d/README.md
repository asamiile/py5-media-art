# kinetic_math_torus_knot_3d_projected_2d

A 3D Torus Knot (p=3, q=7) rendered purely in 2D using custom 3D rotation matrices and perspective projection to circumvent hardware 3D rendering bugs.

## Techniques

Generates 80,000 points forming a thick "tube" around the mathematical knot. Applies 3D rotation and perspective division, then sorts the points by depth (Painter's algorithm) to draw them back-to-front, creating a perfect illusion of voluminous 3D geometry using only 2D circles.

## Palette

"Iridescent Hologram": The tube shimmers through cyan, magenta, and yellow, with depth-based brightness fading into the dark background to create a volumetric fog effect.

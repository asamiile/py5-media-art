# kinetic_algorithmic_flow_field_delaunay_triangulation_2d

A constellation of 500 points flowing through an invisible noise field. A dynamic Delaunay triangulation connects the points, creating an overlapping shattered glass effect.

## Techniques

Uses SciPy's spatial Delaunay triangulation on moving points every frame. The area of each generated triangle dictates its brightness and opacity, emphasizing small, dense clusters over large sparse areas.

## Palette

Highly saturated neon colors transitioning smoothly across the grid over time, rendered with additive blending for a glowing look.

# hyper_sphere_geometric_cross_sections_3d

A massive, glowing 3D hyper-sphere that is continuously sliced by invisible, rotating planes, revealing intricate internal geometries and glowing cross-sections.

## Technique

A dense 3D Fibonacci sphere point cloud. Points are drawn dynamically when they fall within a threshold distance of rotating mathematical planes `Ax + By + Cz + D = 0`. Uses vectorized Numpy operations to mask and render cross-sections efficiently with additive blending.

## Output

Animation (20s @ 60fps)

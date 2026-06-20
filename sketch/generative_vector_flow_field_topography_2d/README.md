# generative_vector_flow_field_topography_2d

A dense 2D vector flow field that draws topography lines instead of moving particles. The lines are drawn statically, but the underlying noise field slowly rotates and shifts its Z-offset over time, causing the drawn lines to writhe and form shifting terrain-like patterns.

## Details

- **Type**: 2D animation
- **Length**: 10 seconds (60fps)

## Technique

A grid of small line segments. The angle of each segment is determined by `py5.os_noise(x, y, z)`. The z parameter increments over time, smoothly evolving the field. The length and color of each segment are mapped to the noise value, creating waves of vibrant colors sweeping across a dark canvas.

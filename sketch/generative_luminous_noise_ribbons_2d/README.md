# Generative Luminous Noise Ribbons 2D

## Description

A generative art piece created using `py5` and `numpy`. The sketch produces a continuous flow of highly detailed, translucent ribbons curving through a complex 3D OpenSimplex noise vector field. By using a dense 2D particle array managed by Numpy and updating them through the noise field, each frame draws low-opacity line segments. Through additive blending, the lines accumulate, forming organic, glowing folds that resemble luminous ethereal ribbons.

## Technical Details

- **Renderer**: Default `py5` 2D renderer.
- **Data Structures**: `numpy` arrays track particle positions and velocities.
- **Motion**: A 3D OpenSimplex noise space is sampled to determine the vector field's curl forces.
- **Visuals**: Additive blending (`py5.ADD`) and low opacity strokes build dense color layers.
- **Compilation**: Individual PNG frames are processed directly via `ffmpeg` into a continuous MP4.

## Output

- **Resolution**: 1920x1080
- **Framerate**: 60 FPS
- **Format**: MP4 (H.264, yuv420p)
- **Duration**: 15 seconds

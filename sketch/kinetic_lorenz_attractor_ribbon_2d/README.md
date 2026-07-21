# kinetic_lorenz_attractor_ribbon_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
A continuously evolving, glowing ribbon tracing the chaotic path of a Lorenz strange attractor. As the attractor spins in 3D space, the glowing trail of a singular particle draws out the famous "butterfly" shape, leaving a fiery echo that fades into darkness.

## Techniques
- **Euler Integration**: 200,000 points of the Lorenz system are precomputed using simple Euler integration ($dt = 0.005$) to ensure extremely fast performance.
- **Numpy 3D to 2D Projection**: To avoid stability issues with OpenGL headless renderers on certain systems, the 3D points are multiplied by a compound rotation matrix (yaw, pitch, roll) and projected onto a 2D canvas entirely using NumPy matrix multiplication.
- **Gradient Trail**: A trailing window of 12,000 points is drawn each frame. The points are iterated in a python loop and rendered with `py5.begin_shape(py5.LINES)`, applying a quadratic color gradient that makes the head of the trail glow bright orange/gold while the tail fades to dark purple.

## Palette
Fiery orange and gold fading into deep dark purple, rendered using `py5.ADD` blend mode.

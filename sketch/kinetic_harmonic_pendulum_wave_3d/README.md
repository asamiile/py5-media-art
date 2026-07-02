# Kinetic Harmonic Pendulum Wave 3D

## Concept
A hypnotic array of suspended pendulums swinging in precise mathematical harmony. This sketch visualizes 100 pendulums with incrementally varying lengths, moving from chaotic noise into sinuous waves, twisting double-helix structures, and eventually returning to synchronized alignment.

## Technical Implementation
- Simulated 100 pendulums using physical harmonic equations (`angle = max_angle * cos(freq * t)`).
- 3D perspective projection onto a 2D canvas without a P3D context.
- Slow camera rotation matrix applied around the Y axis for dynamic depth.
- `py5.lines()` optimized rendering by interlacing origin and point coordinates into a single array matrix.
- ADD blend mode creates accumulated neon glowing trails from the moving pendulum bobs over a dark void background.

## Execution
- `N_Pendulums`: 100
- `FPS`: 60
- `Duration`: 15 Seconds
- `Resolution`: 3840x2160

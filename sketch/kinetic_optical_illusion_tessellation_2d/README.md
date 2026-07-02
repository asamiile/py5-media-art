# Kinetic Optical Illusion Tessellation 2D

## Concept
A dizzying, high-contrast optical illusion where geometric tessellations continuously fold and invert themselves, playing with the viewer's depth perception. The cubes appear to protrude or recede seamlessly based on radial waves of shadow and light propagating from the center.

## Technical Implementation
- Procedurally drawn Escher-like isometric cubes mapped over a hexagonal grid (`py5.quad()`).
- Rhythmically shifting shading and face-rotation parameters using a global trigonometric wave, producing the illusion of 3D geometry flipping from purely 2D operations.
- Radial phase offset creates a continuous outward rippling effect that seamlessly loops over 15 seconds.

## Execution
- `FPS`: 60
- `Duration`: 15 Seconds
- `Resolution`: 3840x2160

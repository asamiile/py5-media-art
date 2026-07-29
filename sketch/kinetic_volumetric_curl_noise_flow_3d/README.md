# kinetic_volumetric_curl_noise_flow_3d

**Date**: 2026-07-24
**Type**: Animation (900 frames, 60fps)

## Concept
A 3D volumetric fluid simulation depicting 500,000 particles advecting through a turbulent vector field. Resembling a cosmic nebula or a swirling galaxy, the particle swarm is shaped by a synthetic 3D curl noise field combined with a central rotational vortex. The entire volumetric cloud spins slowly on a turntable camera axis, revealing its fluid, three-dimensional internal structure.

## Techniques
- **Trigonometric 3D Curl Noise Approximation**: To avoid expensive 3D Perlin noise evaluations across 500,000 points, the divergence-free vector field is approximated via trigonometric wave interference:
  - `vx = sin(1.21·y + t) · cos(0.83·z - 0.5t) + sin(0.5y)`
  - `vy = sin(1.13·z - t) · cos(0.97·x + 0.3t) + cos(0.5z)`
  - `vz = sin(1.37·x + t) · cos(0.71·y - 0.7t) - sin(0.5x)`
- **Central Restoring Vortex**: A radial vortex force vector `(-z, 0, x) / (|pos| + 1.0)` is superimposed on the flow field. This prevents the particles from dispersing endlessly into deep space, maintaining a dense, bounded nebula volume around the origin.
- **Pure Software 3D Engine**: Bypasses OpenGL / `P3D` rendering entirely. Particle transformations (Y-axis turntable rotation), pinhole perspective projection (`fov = H * 0.8`), and non-linear depth falloff (`depth_fade²`) are computed purely in vectorized NumPy array operations.
- **Radial Color Parameterization**: Colors are assigned at initialization based on each particle's initial radial distance from the origin (`r ∈ [0, 5]`), establishing a permanent color identity that highlights internal flow mixing.
- **Direct Pixel Compositing with Exponential Trail Decay**: Points are projected to screen coordinates and composited directly into py5's raw pixel buffer (`np_pixels`) using additive blending. Previous frames undergo an exponential multiply decay (`230/256`), giving the volumetric nebula a glowing, long-exposure trail aesthetic.

## Palette
Bioluminescent Cosmic Nebula:
- **Core / Inner Radius (`r → 0`)**: Hot Magenta (`RGB(255, 0, 0..50)`)
- **Mid Region (`r ≈ 2.5`)**: Deep Purple (`RGB(128, 25, 128)`)
- **Outer Shell (`r → 5`)**: Luminous Cyan (`RGB(0, 50, 255)`)

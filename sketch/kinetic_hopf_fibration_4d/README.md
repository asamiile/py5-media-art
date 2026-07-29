# kinetic_hopf_fibration_4d

**Date**: 2026-07-24
**Type**: Animation (900 frames, 60fps)

## Concept
A visualization of 4-dimensional topology projected into 3D space, revealing the interlocking ring structure of the Hopf fibration. 1,000,000 particles flow continuously across the surface of a Clifford Torus embedded in 4D space. As a pair of independent 4D rotation matrices are applied each frame, the projected shape undergoes a transformation that has no equivalent in 3D geometry: a torus that smoothly turns inside out, forming nested glowing light fibers that weave through each other without intersection.

## Techniques
- **Clifford Torus Parameterization**: Each particle is defined by two independent angles `(θ₁, θ₂)`, placing it on the surface of a Clifford Torus — the product of two unit circles embedded in 4D space. The 4D coordinates are computed as `(cos(θ₁), sin(θ₁), cos(θ₂), sin(θ₂)) / √2`, which ensures the torus lies exactly on the unit 3-sphere S³ in R⁴.
- **Independent 4D Rotations**: Two orthogonal rotation planes are animated simultaneously — the X-W plane and the Y-Z plane — at different angular velocities. Because these planes are fully orthogonal in 4D, the two rotations do not interfere and produce a compound motion that has no analogue in 3D rigid-body rotation.
- **Stereographic Projection (4D → 3D)**: The 4D coordinates are projected to 3D using a stereographic map with pole at W = 1.2. This projection preserves the circle structure of the Hopf fibration: every fiber (a closed orbit on the torus) projects to a circle in 3D, and these circles are all mutually linked, producing the characteristic interlocked-ring topology of the Hopf map.
- **3D Perspective Camera**: The stereographically projected 3D shape is further rotated around the Y axis by a slow camera orbit, then tilted at a fixed angle, and finally projected to 2D screen coordinates via a pinhole perspective model. The two-stage projection (4D→3D→2D) gives the animation a sense of depth within depth.
- **Volumetric Fiber Rendering via Noise**: A small Gaussian noise offset is added to each particle's `(θ₁, θ₂)` angles, giving the mathematically one-dimensional fiber curves a physical thickness. This turns the topology visualization into something resembling glowing neon tubes or plasma filaments.
- **Intrinsic 4D Color Mapping**: Particle color is determined by the combination `(θ₁ + 2·θ₂) mod 2π`, a quantity intrinsic to the particle's position on the torus surface in 4D. Because this value flows with the particle as it moves, neighboring fibers maintain coherent color identities as they sweep through 3D space.
- **Additive Pixel Blending with Trail Decay**: Stars are composited additively into the raw pixel buffer (`np_pixels`) using `np.add.at`, correctly handling multiple particles landing on the same pixel. Each frame, all pixel values are multiplied by `220/256`, producing a persistent luminous trail effect analogous to long-exposure photography.

## Palette
A cyclic three-stop gradient maps Neon Pink → Cyan → Purple → Neon Pink across the intrinsic 4D surface coordinate. The cyclic nature of the colormap matches the cyclic topology of the torus, so that the color transitions remain continuous as particles flow around the surface. Dense fiber regions saturate to white via additive blending, while sparse outer areas remain in deep violet and magenta against a pitch-black background.

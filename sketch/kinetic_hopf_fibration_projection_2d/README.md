# kinetic_hopf_fibration_projection_2d

An animated sequence of glowing rings projected from 4-dimensional space. The Hopf Fibration mathematically maps a 3-sphere (a sphere in 4D space) to a 2-sphere (a standard 3D sphere). By applying stereographic projection, this 4D structure is mapped down into 3D, and then projected again into 2D, revealing beautifully interlocking Villarceau circles.

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
To render the fibration in real time, the algorithm computes 90,000 points spanning 300 discrete rings. The calculation is done across NumPy arrays representing 4D coordinates ($X_1, X_2, X_3, X_4$). The points undergo continuous 4D rotation matrices before being stereographically projected to 3D via $p_{3d} = p_{4d}[0..2] / (1 - p_{4d}[3])$. Finally, they are projected to 2D using a perspective transform. The dense geometry is drawn using `py5.POINTS` combined with an additive blend mode, creating a glowing, ghostly optical effect where all rings perfectly interlock without ever intersecting.

# kinetic_math_spirograph_lissajous_3d

An intricate, kinetic 3D spirograph consisting of a thick ribbon woven from thousands of individual geometric strands, forming complex Lissajous knots that continuously morph and re-weave themselves.

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
The animation generates 400,000 points per frame, distributed across 100 parallel strands to form a volumetric ribbon. The path is defined by a 3D Lissajous curve parametrised by $X, Y, Z$ frequencies. By continuously driving the phase offsets of the equations over time, the knot dynamically unties and weaves itself into new topologies. 
To add texture, high-frequency trigonometric offsets are added to each strand to simulate a braided "cable". The entire 3D structure undergoes rotation and perspective projection. The depth ($Z$-coordinate) drives the color palette, mapping the background geometry to dark purples and foreground geometry to glowing bright cyans, enhancing the 3D volume via additive blending.

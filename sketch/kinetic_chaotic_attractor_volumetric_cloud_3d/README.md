# kinetic_chaotic_attractor_volumetric_cloud_3d

A generative visualization of a custom 3D discrete chaotic attractor, forming an intricate, morphing volumetric cloud of mathematical smoke.

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
This sketch extends the mathematical principles of 2D strange attractors (like Clifford and Peter de Jong) into a third dimension. 300,000 particles are evaluated through a custom system of 3D trigonometric difference equations. Nine independent parameters ($a$ through $i$) govern the topology of the system. By modulating these parameters over time with offset sine waves, the resulting geometry behaves like a living volumetric cloud, continuously folding, collapsing, and expanding.
The dense point cloud undergoes a 3D rotation and perspective projection. It is rendered with heavy motion blur and additive blending. The particles are colored based on their Z-depth relative to the camera—Cyan in the foreground, Magenta in the midground, and Gold in the background—enhancing the illusion of thick, luminous, three-dimensional vapor.

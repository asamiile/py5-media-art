# kinetic_interference_standing_waves_2d

An abstract, kinetic visualization of 2D wave interference patterns, rendered as a glowing, undulating three-dimensional membrane.

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
The animation uses a massive NumPy meshgrid of 640,000 points (800x800 resolution) to represent a continuous membrane. The height ($Z$) of each point is calculated by superimposing the sine waves from 5 distinct, continuously drifting "drop" sources, simulating complex wave interference. The resulting $Z$ coordinate is then used to tilt and project the 2D grid into a 3D perspective using custom 3D rotation matrices. 
To create a luminous, neon aesthetic, the points are sliced into three boolean masks based on their elevation (peaks, valleys, and mid-levels), and colored with intense additive pinks, cyans, and purples. `py5.POINTS` draws the geometry efficiently, and a dark motion-blur pass softens the chaotic high-frequency ripples into smooth moiré-like patterns.

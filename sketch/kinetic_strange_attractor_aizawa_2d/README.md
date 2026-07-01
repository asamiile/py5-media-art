# kinetic_strange_attractor_aizawa_2d

An animated 3D visualization of the Aizawa strange attractor, a chaotic mathematical system known for its beautiful, spherical, tube-like structure. 

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
The animation utilizes NumPy to simultaneously compute the trajectories of 300,000 independent particles moving through the 3D differential equations of the Aizawa attractor:
$dx/dt = (z - b)x - dy$
$dy/dt = dx + (z - b)y$
$dz/dt = c + az - z^3/3 - (x^2 + y^2)(1 + ez) + fzx^3$

To make the structure organic and breathing, parameters $a$ and $c$ are modulated via slow sine waves over time. The 3D coordinates are dynamically rotated and perspective-projected into 2D space. The geometry is colored based on its native $Z$-elevation (Gold at the top, Cyan in the middle, Deep Purple at the bottom) and rendered with dense additive point clouds to create a glowing volumetric form that rotates seamlessly.

# kinetic_lorenz_attractor_butterfly_2d

An animated visualization of a mutating Lorenz strange attractor, demonstrating the iconic "butterfly effect" of chaos theory. 

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
The sketch uses NumPy to concurrently simulate 250,000 particles navigating the Lorenz differential equations:
$dx/dt = \sigma(y - x)$
$dy/dt = x(\rho - z) - y$
$dz/dt = xy - \beta z$

By using a vectorized Euler integration with small time steps, a massive density of points forms the attractor structure instantly. To give the piece kinetic energy, the Rayleigh parameter ($\rho$) continuously drifts, causing the structure to stretch, contract, and chaoticize. A gentle 3D rotation and perspective projection present the dynamic form. 
The wings of the attractor are color-coded (Cyan for the left pole, Magenta for the right pole) using logical masks, and they leave glowing trails using a transparent additive blend mode.

# kinetic_wave_interference_caustics_2d

**Date**: 2026-07-24  
**Type**: Animation (900 frames, 60fps)  

## Concept

A numerical fluid-physics simulation of the 2D Wave Equation ($\frac{\partial^2 u}{\partial t^2} = c(x,y)^2 \nabla^2 u$), capturing complex wave interference patterns and refractive underwater caustics. Five wave emitters orbit in continuous Lissajous trajectories, injecting oscillating ripples into a medium with a non-uniform refractive index. As the wave fronts intersect and refract, constructive interference forms sharp, shimmering networks of caustic light reminiscent of sunlight playing on the floor of a swimming pool or shallow sea.

## Techniques

- **2D Wave Equation & Verlet Integration**:
  Wave dynamics are computed on a $1920 \times 1080$ simulation grid using finite-difference time-domain (FDTD) Verlet integration:
  $$u^{n+1} = 2.0 u^n - u^{n-1} + c(x,y)^2 \nabla^2 u^n$$
  A damping factor of $0.999$ per time step is applied to model natural viscous energy dissipation.

- **Spatially Varying Wave Speed (Refractive Index Landscape)**:
  Rather than a homogeneous domain, the local wave speed $c(x,y)$ varies spatially according to an overlapping low-frequency trigonometric function:
  $$c(x,y) = 0.4 + 0.15 \sin(0.015 x) \cos(0.01 y) + 0.15 \cos(0.007 x + 0.012 y)$$
  Clipped to $[0.1, 0.6]$ for numerical stability under Courant-Friedrichs-Lewy (CFL) conditions, this spatial field acts as invisible "acoustic/optical lenses", bending and focusing propagating wavefronts.

- **9-Point Isotropic Laplacian Stencil**:
  The 2D spatial Laplacian $\nabla^2 u$ is evaluated using a 9-point stencil via `numpy.roll` (orthogonal neighbors weighted by $0.2$, diagonal neighbors by $0.05$, center by $-1.0$). This provides significantly higher spatial isotropy than a 5-point stencil, eliminating square grid alignment artifacts in wave propagation.

- **Lissajous Wave Emitters**:
  Five moving emitters trace out harmonic Lissajous curves across the domain, injecting high-frequency sinusoidal oscillations into localized $5 \times 5$ pixel regions to continuously generate fresh ripple fields.

- **Sub-Stepped Physics Loop**:
  Each rendered frame computes 4 internal physics sub-steps (`STEPS_PER_FRAME = 4`) at $\Delta t = 0.005$, ensuring fine-grained numerical precision and preventing high-frequency wave aliasing.

- **Color Map Lookup & Direct Buffer Rendering (`np_pixels`)**:
  Wave amplitudes $u(x,y) \in [-2.0, 2.0]$ are mapped non-linearly to 256 color indices. The resulting RGBA buffer is scaled $2\times$ to 4K resolution ($3840 \times 2160$) and transferred directly into `py5.np_pixels` for real-time 60fps frame generation.

## Palette

- **Deep Troughs ($v < -0.1$)**: Oceanic deep blue to near-black (`#000000` to `#001E50`).
- **Equilibrium ($ -0.1 \le v < 0.1 $)**: Dark blue transitioning to vibrant cyan (`#001E50` to `#0064B4`).
- **Wave Crests ($ 0.1 \le v < 0.6 $)**: Luminous cyan to electric turquoise (`#0064B4` to `#00C8FF`).
- **Caustic Highlights ($ v \ge 0.6 $)**: Intense constructive interference peaks saturating to pure brilliant white (`#00C8FF` to `#FFFFFF`).

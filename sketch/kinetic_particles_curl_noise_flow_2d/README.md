# kinetic_particles_curl_noise_flow_2d

A kinetic animation depicting perfectly smooth, divergence-free fluid motion created by calculating the analytical curl of a 2D scalar potential field. 

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
Simulating true fluid dynamics for millions of particles is computationally intensive. Instead, this sketch constructs an analytical scalar potential field $\Psi(x, y, t)$ as a superposition of 10 continuous spatial harmonics (sine/cosine waves). By mathematically deriving the curl of this potential ($V_x = \partial \Psi / \partial y$, $V_y = -\partial \Psi / \partial x$), the resulting velocity vector field is guaranteed to be divergence-free ($\nabla \cdot V = 0$). This forces the 300,000 particles to trace out perfectly smooth, incompressible eddies and swirls, exactly like real fluid, without the overhead of Navier-Stokes simulations. The particles wrap seamlessly around the edges of the canvas and leave long additive-blended trails over a motion-blurred background.

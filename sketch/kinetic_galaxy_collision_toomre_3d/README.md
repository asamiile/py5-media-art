# kinetic_galaxy_collision_toomre_3d

**Date**: 2026-07-24
**Type**: Animation (900 frames, 60fps)

## Concept
A 3D astrophysical simulation of a galactic collision using the Toomre Model (restricted 3-body problem). Two supermassive galactic cores attract each other gravitationally while 600,000 orbiting star particles are subjected to their immense tidal forces, tearing both galaxies apart into long, sweeping tidal tails and stellar bridges. A virtual camera slowly orbits the system's center of mass, revealing the full three-dimensional structure of the collision in perspective.

## Techniques
- **Toomre Restricted 3-Body**: The two galactic cores solve a full 2-body gravitational problem between themselves. The 600,000 stars are treated as massless test particles — they feel gravity from both cores but do not exert forces on each other, reducing the complexity from O(N²) to O(N).
- **Keplerian Disk Initialization**: Each galaxy is seeded as a thin rotating disk. Star positions are drawn in polar coordinates and assigned circular orbital velocities via `v = sqrt(G*M/r)`, ensuring the initial disk is in quasi-stable rotation before the encounter begins. Each disk is rotated into an independent 3D orientation using Euler rotation matrices.
- **Symplectic Euler Integration**: Velocity is updated before position each time step, preserving the symplectic structure of Hamiltonian mechanics and avoiding the long-term energy drift that afflicts naive Euler integration. Six physics sub-steps are computed per rendered frame (DT=0.02) for accuracy.
- **Gravitational Softening**: A softening length is added to all distance denominators, preventing numerical blow-up when a star passes very close to a core and setting the minimum resolvable physical scale of the simulation.
- **Perspective Projection with Depth Fading**: All 3D particle positions are projected to 2D screen space each frame using a pinhole camera model. Particles further from the camera are attenuated by a depth-fade factor, reinforcing the volumetric illusion without any 3D graphics API.
- **Additive Pixel Blending via np_pixels**: Rendering bypasses py5's drawing primitives entirely. Stars are written directly into the raw pixel buffer with additive blending, causing dense regions (cores, tidal tail concentrations) to naturally saturate to white while sparse regions remain dim — encoding stellar density as luminosity.
- **Long-Exposure Trail Decay**: Each frame, all pixel values are multiplied by `230/256` before new stars are drawn, simulating the exponential decay of a long-exposure photograph. Rapid stellar motion accumulates into smooth luminous streaks.

## Palette
One galaxy burns in cold **Cyan and deep Blue**, with a hot white core grading outward into cooler hues as a function of each star's initial radial distance. The second galaxy is rendered in **Magenta, Orange, and White**, its warmer chromatic palette suggesting a distinct stellar population. Both collide against a pitch-black deep-space void, with additive blending producing vivid colour mixing at the intersection of the two tidal streams.

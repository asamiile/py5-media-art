# kinetic_spherical_curl_fluid_3d

**Date**: 2026-07-24
**Type**: Animation (900 frames, 60fps)

## Concept
A 3D planetary fluid simulation depicting 600,000 particles swirling across the surface of a sphere, resembling the turbulent atmospheric dynamics and jet streams of a gas giant planet. The particles flow in a divergence-free (incompressible) vector field that remains strictly tangent to the spherical surface, giving rise to persistent vortices and swirling latitudinal bands.

## Techniques
- **Divergence-Free Spherical Vector Field ($\vec{v} = \nabla S \times \hat{n}$)**: A time-varying 3D scalar potential field $S(x,y,z,t)$ is constructed using a linear combination of interfering 3D sine waves and polar vortex terms. Taking the numerical gradient $\nabla S$ and computing its vector cross product with the spherical surface normal $\hat{n} = \vec{p}/R$ yields a velocity vector $\vec{v}$ that is mathematically guaranteed to be tangent to the sphere ($\vec{v} \cdot \hat{n} = 0$) and divergence-free ($\nabla \cdot \vec{v} = 0$), preserving particle density across the fluid.
- **Thermal Brownian Noise & Radial Reprojection**: Microscopic Langevin noise is added to the particle positions each physics step to prevent collapse into 1D filaments, and positions are reprojected onto the sphere ($R = 400.0$) via normalisation to enforce strict surface containment over time.
- **Latitude-Based Kinetic Palette**: Particles are shaded according to their absolute latitude ($|z|/R$). The equator features deep blues and purples, shifting through gold and fiery orange in mid-latitudes, and culminating in bright white polar vortices.
- **Software Depth Filtering & Edge Fading**: Particles on the back hemisphere ($z_{cam} \ge 50$) are culled. Remaining front-hemisphere particles receive an edge-fade weighting near the sphere's limb ($z_{cam} \approx 0$), softening the silhouette and preventing visual harshness at the sphere boundary.
- **Direct Pixel Buffer Compositing with Trail Decay**: Projected 2D screen positions are composited directly into py5's raw pixel buffer (`np_pixels`) using additive blending. Each frame, all existing pixels are scaled by `210/256` to create exponential trail decay, imparting a long-exposure astrophotographic feel.

## Palette
Gas Giant atmospheric theme:
- **Equator**: Deep Indigo / Purple (`RGB(0..150, 0, 100..255)`)
- **Mid-latitudes**: Warm Gold / Orange (`RGB(150..255, 0..200, 255..55)`)
- **Poles**: Bright White / Yellow (`RGB(255, 200..255, 55..255)`)

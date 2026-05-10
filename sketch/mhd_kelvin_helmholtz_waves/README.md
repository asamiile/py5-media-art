# MHD Kelvin-Helmholtz Waves

A simulation of Magnetohydrodynamic (MHD) Kelvin-Helmholtz instabilities in a magnetized plasma shear layer.

![MHD Kelvin-Helmholtz Waves](mhd_kelvin_helmholtz_waves_p1.png)

## Concept
This artwork visualizes the "billowing" interface between two fluids with different velocities, a classic fluid dynamics instability known as Kelvin-Helmholtz (KH). In an MHD context, the presence of a magnetic field (modeled here via a tension proxy) resists the vertical displacement, leading to more elongated, filamentary vortex structures compared to purely hydrodynamic flows.

The aesthetic follows the "Beautiful Night Sky" theme, with particles representing glowing plasma filaments in a cosmic shear flow.

## Technical Details
- **Simulation**: Vectorized NumPy advection of 60,000 particles through a shear velocity field ($v_x = U \tanh(y/\delta)$) with periodic boundary conditions.
- **Physics**: Includes a magnetic tension proxy that provides a restoring force to vertical perturbations, and a sinusoidal phase-shifted perturbation to trigger the billows.
- **Rendering**: P2D additive blending with persistence-based motion blur to create soft, glowing trails.
- **Palette**: "Deep Amethyst / Luminous Teal / Molten Gold" with color mapping based on initial vertical position.

## Metadata
- **Duration**: 15 seconds
- **FPS**: 60
- **Resolution**: 4K (3840x2160)
- **Engine**: py5 (Processing for Python)

# mhd_accretion_turbulence

A high-energy visualization of Magnetohydrodynamic (MHD) turbulence within a black hole's accretion disk.

## Concept
The accretion disks around compact objects are sites of violent plasma dynamics. This piece captures the turbulent flow driven by the Magneto-Rotational Instability (MRI), where magnetic fields twist and shear the orbiting material into complex, incandescent filaments.

## Technique
- **Simulation**: 180,000 particles in a rotating disk configuration. Forces include Keplerian gravity, differential rotation, and a "magnetic tension" proxy (sinusoidal warping of velocity vectors).
- **Turbulence**: Stochastic oscillations and magnetic ropes effect simulate the MRI, creating clumps and high-velocity nodes.
- **Rendering**: Multi-pass additive point rendering. Brightness and color are mapped to local kinetic energy (velocity magnitude).
- **Palette**: "Incandescent Orange / Plasma Blue / Obsidian Black" against a star-dusted void.

## Format
- **Animation**: 10 seconds @ 60fps
- **Resolution**: 3840x2160 (4K)
- **Engine**: py5 (Python implementation of Processing)

# ginzburg_landau_vortices

A generative visualization of topological defects in a complex scalar field, governed by the Time-Dependent Ginzburg-Landau (TDGL) equation.

## Theme
- Superconductivity, superfluidity, and phase transitions.
- "Celestial Teal / Nebula Violet / Starfire Gold" palette.
- Emergent vortex dynamics and turbulent flow.

## Technique
- **Field Simulation**: Solves the TDGL equation on a 128x128 grid, capturing the formation and interaction of quantum vortices (phase singularities).
- **Particle Advection**: 40,000 particle tracers driven by the supercurrent (imaginary part of the conjugate field gradient).
- **3D Projection**: Manual perspective projection of particles across a volumetric space (z-depth 0-800).
- **Batch Rendering**: Particles are batched by phase angle to optimize rendering calls with additive blending and HSB spectral mapping.

## Controls
- Run the script to generate a 10-second 4K animation at 60fps.
- Previews are saved as `ginzburg_landau_vortices_p1.png`.

# Tidal Wave Propagation

A dynamic visualization of seismic energy radiating outward through ocean water as expanding concentric waves, inspired by tsunami generation and propagation.

## Visual Concept

A central epicenter erupts with water displacement that radiates outward in expanding rings. Bright cyan and aqua wave crests rise above the dark ocean surface, gradually dissipating as they travel. The animation captures the relentless energy transfer of seismic waves through water.

## Technical Details

- **Format**: Animation (20s @ 60fps, 4K/3840×2160)
- **Algorithm**: 2D wave equation simulation using Laplacian diffusion
- **Grid Resolution**: 200×120 cells
- **Technique**: 
  - Laplacian-based wave propagation (0.15 coefficient)
  - Velocity-based particle dynamics
  - Reduced damping (0.975) for energy preservation
  - Periodic re-excitation pulses for sustained activity
  - Depth-based color gradient rendering
  - Foam particle effects at wave crests

## Color Palette

- **Background**: Deep ocean navy (#0d1b3d)
- **Dominant (60%)**: Gradient from deep cyan (#0088cc) to bright aqua (#00ddff)
- **Secondary (30%)**: Seafoam white with translucent highlights
- **Accent (10%)**: Golden light refraction on wave crests
- **Mood**: Cold/Precise with Neon energy

## Conceptual Theme

This work visualizes water wave propagation from seismic disturbance, exploring how energy moves through fluid media. The expanding concentric pattern captures both the mathematics of wave physics and the dramatic visual impact of tsunamis crossing open ocean.

Distinct from bioluminescent_shear_tide (advection-based) and water_caustics by focusing on large-scale wave geometry rather than small-scale fluid dynamics.

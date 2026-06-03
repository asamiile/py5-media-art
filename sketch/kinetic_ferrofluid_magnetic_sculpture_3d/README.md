# kinetic_ferrofluid_magnetic_sculpture_3d

## Details
- **Date**: 2026-06-03
- **Format**: Animation (15s @ 60fps)
- **Theme**: Dark, oily ferrofluid spiking and reacting dynamically to a shifting magnetic field in 3D.
- **Technique**: A high-density 3D sphere is dynamically deformed using 4D OpenSimplex noise mapped to spherical coordinates. To simulate the iconic sharp spikes of ferrofluid, the noise values are processed with an absolute power function (`abs(noise)**4`), causing sharp peaks to emerge organically from the smooth base. The mesh is rendered with `py5.TRIANGLE_STRIP`. Material properties are tuned for high specularity (glossiness), interacting with multiple directional and point lights to create realistic reflections and shadows.
- **Color palette**:
  - Background: Stark Clinical White / Light Grey
  - Dominant (60%): Glossy Obsidian Black (the fluid)
  - Secondary (30%): Silver / Metallic Highlights
  - Accent (10%): Magnetic Blue (very subtle under-lighting)
  - Mood: industrial / organic / physical

## Description
An animated 3D simulation of a massive globule of ferrofluid suspended in a clinical white environment. As an invisible, shifting magnetic field passes through the space, sharp, organic spikes of glossy obsidian liquid erupt and recede across its surface. High-contrast specular highlights gleam along the shifting curves, while a faint, magnetic blue under-light hints at the invisible forces driving the fluid's hypnotic, mechanical dance.

# nucleosynthesis_fusion_core

A 3D simulation of stellar nucleosynthesis, capturing the turbulent plasma convection and nuclear fusion processes inside a massive star.

## Description

A churning, incandescent heart of a giant star; a dense sea of electric blue nuclei collide and ignite in spectacular bursts of gold and violet light, slowly transforming the core into a rich, multi-layered tapestry of heavier elements through a complex, toroidal convection field.

## Technique

- **Stellar Plasma Physics**: 3D high-velocity particle simulation (150,000 points) with a softened central gravity model and convective toroidal flow.
- **Nucleosynthesis Stages**: Elemental transformation logic (Hydrogen -> Helium -> Carbon -> Oxygen) based on collision probability and proximity to the stellar center.
- **Fusion Events**: Real-time generation of "gamma-ray" streaks and volumetric glows triggered by successful fusion events.
- **Rendering**: Optimized vectorized particle rendering using `py5.points()` for high-density simulation. Features multi-pass additive glows for the stellar core.
- **Format**: 10-second animation @ 60fps, 4K resolution.

## Preview

![preview_p1](preview_p1.png)

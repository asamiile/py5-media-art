# kinetic_reaction_diffusion_advection_2d

![Preview](kinetic_reaction_diffusion_advection_2d_p1.png)

## Metadata
- **Date**: 2026-08-09
- **Theme**: Bioluminescent cells spawning in a nutrient-rich warm current, undergoing morphogenetic reaction-diffusion while being slowly drifted by a warm thermal wind.
- **Technique**: Gray-Scott Reaction-Diffusion system coupled with a dynamic semi-Lagrangian advection velocity field driven by multi-scale Perlin noise.

## Concept
A warm, organic cellular fabric that constantly divides and mutates. The cell spots spawn in high-density gold and emerald green, leaving traces of deep plum as they dissolve and drift under a flowing, thermal-advection wind.

## Technical Details
- **Renderer**: Custom direct-pixel rendering using `py5.np_pixels`
- **Simulation**: Vectorized Gray-Scott PDE updates with periodic rolls, advected back in time using a bilinear interpolation semi-Lagrangian solver.
- **Visuals**: Multi-phase threshold color mapping (Solar Gold -> Emerald Green -> Warm Plum)
- **Animation**: 15 seconds @ 60 FPS (900 frames)

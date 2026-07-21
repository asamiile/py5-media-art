# kinetic_kaleidoscopic_mandala_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
A hypnotic, evolving geometric pattern that draws heavily on the aesthetics of sacred geometry and kaleidoscopes. The system relies on simple local rules combined with deep global symmetries to produce an incredibly complex structure.

## Techniques
- **Noise-Driven Agents**: 150 independent agents drift around the canvas in polar coordinates. Their radius and angle are smoothly perturbed by OpenSimplex noise fields (`py5.os_noise`), giving them an organic, wandering behavior.
- **Kaleidoscopic Rendering**: Instead of rendering each agent once, its position is drawn 24 times per frame. The canvas is conceptually divided into 12 "slices" (12-fold rotational symmetry). Within each slice, the agent's path is drawn both normally and mirrored, creating perfect geometric reflections.
- **Trail Dynamics**: The agents are categorized into three "tiers" (slow large gold, fast tiny violet, medium amber) which create a layered visual texture. A low-opacity background clear leaves long, fading trails, while `py5.ADD` blending ensures the densest areas of the mandala glow with an intense, fiery light.

## Palette
Rich gold, amber, and deep violet on a pitch-black background.

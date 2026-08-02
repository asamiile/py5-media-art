# kinetic_reiter_snowflake_growth_2d

**Date**: 2026-07-31  
**Type**: Animation (1200 frames, 60fps)  

## Concept

A 4K kinetic visualization of Reiter's offset-row hexagonal lattice diffusion model (Reiter 1996), illustrating the growth of a six-fold symmetric snowflake crystal. Vapor diffuses across a freezing space, accumulating along receptive boundary cells. As saturation limits are breached, ice crystallization propagates outwards. To capture the temporal evolution of the dendritic growth, cells are colored dynamically based on their freeze timestamp: early core nodes freeze in deep bioluminescent purples, transitioning outwards through electric cyans to ice-white tips in the foreground, all floating against a dark cosmic void.

## Techniques

- **Reiter (1996) Hexagonal Diffusion PDE**:
  Water vapor $v(x,y)$ diffuses through empty space:
  $$\frac{\partial v}{\partial t} = \frac{\alpha}{6} \nabla^2 v$$
  evaluated on an offset-row hexagonal grid where even and odd rows sum neighbors selectively. Receptive boundary cells touching existing ice gather vapor at rate $\gamma = 0.001$ per step, solidifying when $v(x,y) \ge 1.0$.

- **Temporal Color-Gradient Mapping (Freeze Contours)**:
  Rather than rendering a uniform color, the frame count when each cell crystallized is tracked in a `freeze_time` grid. The ice is colored dynamically by mapping this timestamp to a gradient: early core (`#501478` Deep Purple) -> mid branches (`#00e5ff` Cyan) -> late tips (`#c8f5ff` Ice Blue/White).

- **Centered 1:1 Aspect Ratio Projection**:
  To prevent stretching on the widescreen 4K canvas, a centered $1:1$ screen-to-grid mapping index vector is precomputed in `setup()`, matching the hexagonal grid dimensions to the height of the screen and masking out-of-bounds horizontal margins.

- **Vapor Supersaturation Glow**:
  Background cells are rendered with variable blue-cyan opacity proportional to their local vapor supersaturation, creating a glowing thermal/chemical field halo around the growing snowflake.

## Palette

- **Background**: Deep Obsidian Void (`#03050c`).
- **Crystal Core (Early Freeze)**: Deep Purple/Magenta (`#501478`).
- **Crystal Mid-Branches (Mid Freeze)**: Electric Cyan (`#00e5ff`).
- **Crystal Outer Tips (Late Freeze)**: Glacial Ice Blue / White (`#c8f5ff`).

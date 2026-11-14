# cobalt_foliation_shear

## Overview
A 4K (3840×2160) generative video artwork exploring **Reeb foliations and symplectic shear strata** across a diagonally swept manifold (`27°` inclination). Over an 18-second (1080-frame @ 60fps) multi-act cycle, parallel foliation leaves nucleate across 9 alternating shear bands, bend into homoclinic saddle whorls, and re-laminate into harmonic equilibrium.

## Visual & Technical Highlights
- **Genre**: Mathematical / Abstract Topology
- **Composition Archetype**: Stratified Horizon / Diagonal Sweep
- **Motion Archetype**: Multi-Act Temporal Evolution
- **Palette**: Deep Forest Viridian (`#0a3830`), Cobalt Ultramarine (`#132c66`), Emerald Teal (`#126862`), Burnt Sienna (`#d94e28`), Coral Vermilion (`#f06438`), Cadmium Gold (`#f4b024`), Warm Ivory (`#f6efe2`).
- **Techniques**: Fragment shader (`cobalt_foliation_shear.glsl`) computing continuous Reeb foliation leaves and separatrix ridges, 162 vectorized holonomy ribbons and hyperbolic saddle-node markers batched via `py5.QUADS` / `py5.vertices`, and `PostFX` finishing.

## Run
```bash
uv run python sketch/cobalt_foliation_shear/main.py
```


# dendrite_rime_veins

## Overview
- **Genre**: Atmospheric / Painterly / Color Field
- **Composition Archetype**: Emergent Network / Boundary-to-Interior Growth
- **Motion Archetype**: Spatial Camera / Depth Traversal
- **Palette Family**: Deep Nocturnal Monochrome + Single Accent
- **Format**: Animation (`21s (1260 frames @ 60fps)`, 3840×2160 4K)
- **Technique**: `P2D + GLSL + PostFX`

## Concept & Visual Architecture
`dendrite_rime_veins` unfolds across a deep nocturnal indigo and charcoal color field (`#0a0d14`–`#161c28`) with silver-frost tonal gradations (`#48576f`, `#c2d0e4`, `#ecf3fc`) and a single restrained warm amber-gold accent (`#f59332`).

Three parallax depth layers of domain-warped Voronoi rime-crystal veins in GLSL (`dendrite_rime_veins.glsl`) and 36 boundary-nucleated dendritic trees in `py5` propagate inward from all four canvas edges toward the open interior while the camera drifts smoothly through depth space. Colliding filament tips and triple-junction crystallization fronts ignite with warm amber sparks.

## Run
```bash
uv run python sketch/dendrite_rime_veins/main.py
```


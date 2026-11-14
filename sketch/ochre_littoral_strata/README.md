# ochre_littoral_strata

## Overview
- **Genre**: Atmospheric / Painterly / Color Field
- **Composition Archetype**: Stratified Horizon / Diagonal Sweep
- **Motion Archetype**: Poly-Rhythmic Phase Interference
- **Palette Family**: High-Key Mineral & Washi (Full-Canvas Light)
- **Format**: Animation (`20s (1200 frames @ 60fps)`, 3840×2160 4K)
- **Technique**: `P2D + GLSL + PostFX`

## Concept & Visual Architecture
`ochre_littoral_strata` unfolds across a 100% full-canvas high-key warm alabaster and raw linen paper ground (`#ede8dc`–`#e5dfcf`). Eight diagonally swept mineral wash horizons in raw ochre (`#ca8a2a`), burnt sienna (`#b84c31`), celadon sage (`#48746e`), and iron-gall slate (`#263640`) undergo poly-rhythmic phase interference driven by three harmonic wave trains drifting at counter-propagating velocities.

Over the wet-into-wet GLSL pigment diffusion and granulation field, 28 calligraphic capillary tide-line ribbons and mineral pigment stipple nodes trace the shifting interference crests using batched `py5.QUADS` geometry.

## Run
```bash
uv run python sketch/ochre_littoral_strata/main.py
```


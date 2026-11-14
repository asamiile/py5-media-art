# kasuri_shuttle_wavefronts

## Overview
- **Genre**: Textile / Calligraphy / Procedural Craft
- **Composition Archetype**: Stratified Horizon / Diagonal Sweep
- **Motion Archetype**: Directional Advection & Traveling Wavefronts
- **Palette Family**: High-Key Mineral & Washi (Full-Canvas Light)
- **Format**: Animation (`17s (1020 frames @ 60fps)`, 3840×2160 4K)
- **Technique**: `P2D + GLSL + PostFX`

## Concept & Visual Architecture
`kasuri_shuttle_wavefronts` unfolds across a 100% full-canvas high-key warm kozo washi paper ground (`#eee8db`–`#e2dac9`). Seven diagonally swept kasuri (ikat) resist-dyed textile strata in iron-gall slate (`#24333d`), mineral indigo (`#324e62`), burnt terracotta sienna (`#bc4e30`), raw gold ochre (`#ce8e2a`), and celadon sage (`#46736c`) undergo continuous directional advection and traveling shed wavefronts.

In GLSL (`kasuri_shuttle_wavefronts.glsl`), feathered ikat step-shifts and diagonal twill micro-ribs propagate along the seven horizons. Layered above in `py5`, 35 warp ribbons and 420 weft-shuttle thread segments advect seamlessly across the diagonal weave using batched `py5.QUADS`.

## Run
```bash
uv run python sketch/kasuri_shuttle_wavefronts/main.py
```


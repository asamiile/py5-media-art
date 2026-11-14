# escarpment_halftone_strata

## Overview
- **Genre**: Atmospheric / Painterly / Color Field
- **Composition Archetype**: Stratified Horizon / Diagonal Sweep
- **Motion Archetype**: Spatial Camera / Depth Traversal
- **Palette Family**: Risograph Overprint Spot Inks
- **Format**: Animation (`16s (960 frames @ 60fps)`, 3840×2160 4K)
- **Technique**: `P2D + GLSL + PostFX`

## Concept & Visual Architecture
`escarpment_halftone_strata` explores a diagonally swept atmospheric escarpment rendered in authentic Risograph spot-ink overprint across a full-canvas warm cream paper ground (`#f0e9dc`–`#e7dfd0`). Nine stratified horizons in translucent fluorescent coral (`#f25240`), peacock teal (`#10968c`), and deep federal indigo (`#1c2a62`) undergo seamless spatial camera depth traversal from the distant upper horizon toward the foreground.

In GLSL (`escarpment_halftone_strata.glsl`), angled halftone dot screens and slight drum registration offsets multiply subtractively on the warm paper. Layered above in `py5`, 27 misregistered 3-channel spot-ink contour ribbons and halftone stipple ridges accentuate the advancing topographic escarpments.

## Run
```bash
uv run python sketch/escarpment_halftone_strata/main.py
```


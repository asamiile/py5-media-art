# turing_chemotaxis_tesserae

## Overview
- **Genre**: Organic / Morphogenesis
- **Composition Archetype**: Full-Canvas Polyptych / Rhythmic Matrix
- **Motion Archetype**: Directional Advection & Traveling Wavefronts
- **Palette Family**: Mid-Tone Atmospheric Dusk / Celadon Slate
- **Format**: Animation (`19s (1140 frames @ 60fps)`, 3840×2160 4K)
- **Technique**: `P2D + GLSL + PostFX`

## Concept & Visual Architecture
`turing_chemotaxis_tesserae` organizes the 3840×2160 frame into an edge-to-edge 5×3 rhythmic matrix of 15 morphogenetic reaction-diffusion domains set on a mid-tone atmospheric dusk and celadon-slate ground (`#2c3840`–`#3d4e48`). Each tessera develops a distinct anisotropic activator-inhibitor Turing wave wavenumber and shear orientation while a global reaction wavefront sweeps diagonally across the entire matrix.

Layered over the GLSL reaction-diffusion field, 150 chemotactic wavefront ribbons and 360 advecting catalyst droplets glide across the 15 cellular domains in soft chalk (`#ebe6da`), misty celadon-teal (`#82a8aa`), warm amber-ochre (`#e49636`), and terracotta (`#ce5e40`).

## Run
```bash
uv run python sketch/turing_chemotaxis_tesserae/main.py
```

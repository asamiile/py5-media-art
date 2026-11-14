# heterodyne_amber_chorus

## Overview
- **Genre**: Signal / Glitch / Digital Artifacts
- **Composition Archetype**: Full-Bleed Continuous Field
- **Motion Archetype**: Poly-Rhythmic Phase Interference
- **Palette Family**: Rich Saturated Color Field
- **Format**: Animation (`15s (900 frames @ 60fps)`, 3840×2160 4K)
- **Technique**: `P2D + GLSL + PostFX`

## Concept & Visual Architecture
`heterodyne_amber_chorus` spans the entire 3840×2160 canvas as a continuous full-bleed heterodyne frequency-modulation (FM) interference field. Across a rich saturated color field of deep ultramarine (`#0a133c`–`#1e3eb8`), crimson magenta (`#b81e6c`), signal vermilion (`#ec4828`), and luminous amber gold (`#f8b224`), four directional FM wave lattices drift at poly-rhythmic harmonic temporal ratios (`1:2:3:4`) while horizontal scanline phase-slips shear the carrier field.

Layered over the GLSL heterodyne beat-interference shader, 44 continuous edge-to-edge vector carrier ribbons and phase-pinched harmonic bridge struts trace the evolving interference antinodes using batched `py5.QUADS` and `py5.LINES`.

## Run
```bash
uv run python sketch/heterodyne_amber_chorus/main.py
```


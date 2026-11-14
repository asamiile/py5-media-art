# eikonal_linen_shocks

## Overview
A 4K (3840×2160) generative video artwork exploring **boundary-nucleated Eikonal wavefront propagation and Rankine-Hugoniot medial-axis shock networks** across a 100% full-canvas high-key raw linen ground (`#ede8dc`–`#e4ddd0`). Sixteen perimeter wave sources launch inward-traveling wavefronts that collide in the interior, forming sharp medial-axis shock ridges and branching fracture veins over a 20-second (1200-frame @ 60fps) seamless loop.

## Visual & Technical Highlights
- **Genre**: Physical / Micro-Kinetic
- **Composition Archetype**: Emergent Network / Boundary-to-Interior Growth
- **Motion Archetype**: Directional Advection & Traveling Wavefronts
- **Palette**: Raw Alabaster Linen (`#ede8dc`–`#e4ddd0`), Iron-Gall Slate (`#243440`), Burnt Terracotta (`#b84a2e`), Raw Gold Ochre (`#c98826`), Malachite Sage (`#387268`).
- **Techniques**: 16-source Eikonal arrival-time solver and Rankine-Hugoniot medial-axis shock bisector contours in GLSL (`eikonal_linen_shocks.glsl`), 256 boundary-to-interior shock-deflected filaments batched via `py5.QUADS` / `py5.vertices`, and `PostFX` finishing.

## Run
```bash
uv run python sketch/eikonal_linen_shocks/main.py
```


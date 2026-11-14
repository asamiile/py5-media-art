# kam_resonance_tori

## Overview
A 4K (3840×2160) generative video artwork exploring **Kolmogorov-Arnold-Moser (KAM) invariant tori, resonance island chains, and symplectic phase-space flows** across a 100% full-bleed mid-tone atmospheric dusk and celadon-slate field (`#2c3840`–`#405c5a`). Over a 24-second (1440-frame @ 60fps) cycle, 2,800 divergence-free Hamiltonian tracers accumulate persistent calligraphic trails around undulating invariant tori and nested 3:2 resonance islands.

## Visual & Technical Highlights
- **Genre**: Mathematical / Abstract Topology
- **Composition Archetype**: Full-Bleed Continuous Field
- **Motion Archetype**: Persistent Trail Accumulation & Decay
- **Palette**: Atmospheric Dusk Slate (`#2c3840`), Celadon Sage (`#405c5a`), Misty Seafoam (`#8eb8b4`), Soft Chalk (`#f2ede0`), Warm Golden Amber (`#f0a438`), Coral Terracotta (`#d86242`).
- **Techniques**: Vectorized symplectic Hamiltonian flow ($\partial H/\partial y, -\partial H/\partial x$) for 2,800 particles and instantaneous KAM invariant-torus / resonance-island contours batched via `py5.QUADS` / `py5.vertices` in pure `P2D` with persistent translucent frame decay (`fill(44, 56, 64, 11)`).

## Run
```bash
uv run python sketch/kam_resonance_tori/main.py
```


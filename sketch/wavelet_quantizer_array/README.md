# wavelet_quantizer_array

## Overview
- **Genre**: Signal / Glitch / Digital Artifacts
- **Composition Archetype**: Full-Canvas Polyptych / Rhythmic Matrix
- **Motion Archetype**: Spatial Camera / Depth Traversal
- **Palette Family**: Deep Nocturnal Monochrome + Single Accent
- **Format**: Animation (`18s (1080 frames @ 60fps)`, 3840×2160 4K)
- **Technique**: `P2D + GLSL + PostFX`

## Concept & Visual Architecture
`wavelet_quantizer_array` visualizes a 4×3 full-canvas rhythmic matrix of 2D wavelet subbands, Walsh-Hadamard square-wave basis packets, and dead-zone uniform quantizers. Each of the twelve cells operates at a distinct spatial frequency harmonic and undergoes cyclic camera depth traversal along its subband axis while horizontal packet-slip shears quantize the underlying carrier field.

Layered over the GLSL wavelet interference field, crisp vector staircase transfer curves and residual error stems track live quantization distortion between continuous harmonic waves and discrete step levels. The palette pairs deep obsidian and cool slate monochromes (`#0a0c11`, `#181e2a`, `#8f9eb5`, `#e6edf7`) with a single high-energy burnt-signal amber accent (`#ff5e24`) that ignites along quantization residual spikes and bit-run leading edges.

## Run
```bash
uv run python sketch/wavelet_quantizer_array/main.py
```


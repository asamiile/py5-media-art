# sumi_kuroshio_plumes

## Overview
- **Genre**: Atmospheric / Painterly / Color Field
- **Composition Archetype**: Full-Bleed Continuous Field
- **Motion Archetype**: Persistent Trail Accumulation & Decay
- **Palette Family**: Deep Nocturnal Monochrome + Single Accent
- **Format**: Animation (`21s (1260 frames @ 60fps)`, 3840×2160 4K)
- **Technique**: `P2D CPU/NumPy` (Vectorized curl-streamfunction advection + persistent frame-decay buffer)

## Concept & Visual Architecture
`sumi_kuroshio_plumes` spans the entire 3840×2160 canvas as a continuous nocturnal ink-wash and oceanic vortex field. Across a deep sumi-indigo ground (`#0b0e15`), 2,400 divergence-free curl-vortex brush filaments advect through a time-varying 4-mode harmonic streamfunction $\psi(x, y, t)$.

Through persistent translucent frame-fading accumulation (`fill(11, 14, 21, 5)`), wide sumi-graphite washes (`#323d52`), silver-mist midtones (`#7b8ea8`), and fine moonlit-chalk calligraphic filaments (`#dce6f5`) layer into luminous atmospheric plumes, punctuated by a single restrained vermilion-cinnabar accent (`#f04e32`) along high-vorticity shear streams.

## Run
```bash
uv run python sketch/sumi_kuroshio_plumes/main.py
```


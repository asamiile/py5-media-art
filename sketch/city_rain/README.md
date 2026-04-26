# city_rain

**Theme**: urban, night, atmosphere, rain, reflection, neon  
**Date**: 2026-04-26

## Description

A procedurally generated nocturnal cityscape viewed from street level in the rain. The scene is composed in six layers rendered as a numpy float32 image:

1. **Sky** — a near-black blue-grey gradient deepening toward zenith
2. **Buildings** — four depth layers (back→front) of randomly generated rectangular towers, each slightly brighter and taller than the layer behind; a subtle parapet highlight caps each building
3. **Windows** — a grid of 5×7 px windows on every building facade, with 10–35% lit (depending on depth layer) and five colour types: amber, cool white, orange, neutral, fluorescent green
4. **Neon signs** — 5–8 vivid horizontal bars (hot pink, electric cyan, amber, purple, neon green) placed on building facades
5. **Wet pavement** — the lower 40% reflects the sky layer flipped vertically, asymmetrically blurred (σ: 1.0 vertical, 5.5 horizontal), and sinusoidally ripple-warped before fading toward the bottom
6. **Rain** — exponential random field filtered to thin vertical streaks (σ: [14, 0.35]) with a slight horizontal roll for diagonal slant

Post-processing: additive bloom (gaussian of bright mask, σ = 14), horizon atmospheric glow, vignette, and a γ = 0.86 power curve.

## Technique

- **Building generation**: back-to-front layered rectangles, per-layer brightness/height/window-density parameters
- **Reflection**: `sky[::-1]` → asymmetric `gaussian_filter` → sinusoidal ripple `np.roll` per row → fade mask
- **Rain**: `RNG.exponential` + `gaussian_filter([14, 0.35])` + diagonal roll
- **Bloom**: `(scene − 0.18).clip(0) → gaussian(σ=14)` added back at 0.55×

## Parameters

| Constant | Value |
|---|---|
| Horizon position | 60% of height |
| Building depth layers | 4 |
| Neon signs per run | 5–8 |
| Lit window fraction | 10–35% by layer |
| Bloom radius | σ = 14 px |
| Preview size | 1920 × 1080 |
| Output size | 3840 × 2160 |

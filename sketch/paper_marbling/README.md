# paper_marbling

**Theme**: craft, textile, fluid, optics, Turkish ebru, Ottoman art  
**Date**: 2026-04-26

## Description

A simulation of *ebru* — Turkish paper marbling — using the classical mathematical model of ink behaviour on a water surface. The pattern emerges from two physical operations applied in sequence to a normalised coordinate grid:

1. **Ink-drop expansion** (7–11 drops): each drop placed at a random position pushes all existing ink radially outward. The expansion formula is exact:
   `new_d = sqrt(d² + r²)` where `d` is the distance from the drop centre and `r` is the drop radius. This stretches the colour stripes into the characteristic starburst / teardrop shapes seen in traditional ebru.

2. **Comb strokes** (5–9 passes): alternating horizontal and vertical comb passes each displace one coordinate by a sinusoidal function of the other:
   `wy += A · sin(2π · wx / λ + φ)` or `wx += A · sin(2π · wy / λ + φ)`.
   Amplitude decays by 0.82 each pass, generating fine detail on top of coarse strokes.

A six-colour peacock palette (peacock blue · warm cream · emerald · antique gold · deep burgundy · midnight navy) is linearly interpolated across five repeating stripe cycles. Fine Gaussian grain and a mild vignette simulate the surface texture of marbled paper.

## Technique

- **Drop expansion**: `new_d = sqrt(d² + r²)` per drop, vectorised over full canvas
- **Comb warp**: alternating x/y sinusoidal displacement, amplitude decaying 0.82ˢᵗʳᵒᵏᵉ
- **Colour**: continuous linear interpolation between adjacent PALETTE entries; 5 palette repeats per canvas
- **Post**: fine gaussian grain (σ = 0.5) + mild vignette (0.30 · r²)

## Parameters

| Constant | Range / Value |
|---|---|
| Ink drops | 7–11 |
| Drop radius | 4–14% of canvas height |
| Comb strokes | 5–9 |
| Comb wavelength | 7–22% of canvas |
| Palette | 6 jewel tones (peacock / cream / emerald / gold / burgundy / navy) |
| Preview size | 1920 × 1080 |
| Output size | 3840 × 2160 |

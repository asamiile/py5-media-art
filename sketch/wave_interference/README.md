# Wave Interference (Precision Instrument)

![Preview](preview_p1.png)

## Metadata
- **Date**: 2026-05-05 (Polish v3)
- **Theme**: Physics, Wave Interference, Precision Measurement
- **Technique**: Vectorized Plane Wave Superposition, High-Resolution P2D Buffer, Non-linear Contrast Mapping

## Concept
A study of complex wave interference patterns, presented as if through a high-precision optical measurement instrument. The "Sapphire & Mercury" palette highlights the interplay of constructive and destructive interference with surgical clarity.

## Technical Details
- **High-Resolution Computation**: The field is computed using NumPy at full output resolution (up to 4K), eliminating the "blurriness" of low-resolution upscaling.
- **Contrast Polish**: Implemented a power-law contrast mapping to sharpen the wave edges and enhance the optical depth.
- **Instrument Overlay**: Added a technical grid and source crosshair markers to reinforce the measurement aesthetic.
- **Palette**: Deep Sapphire, Mercury White, and Obsidian Blue.

## History
- **v1/v2**: Initial standing wave patterns; noted as "too blurry" due to low-resolution simulation.
- **v3 (Current)**: Full-resolution rewrite with enhanced contrast and technical UI.

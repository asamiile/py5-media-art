# hyper_chromatic_glitch_fold

**Date**: 2026-05-22
**Format**: 15s 4K/60fps MP4
**Algorithm/Technique**: Vectorized recursive grid subdivision with pseudo-random chromatic displacement, localized horizontal tearing (row-shifting), and high-frequency noise injection. Multi-pass RGB channel splitting to simulate severe chromatic aberration. Rendered directly into the py5 pixel buffer.

## Concept

A high-density data matrix folding and tearing itself apart, bleeding brilliant spectral colors as its structural integrity collapses under recursive glitches.

## Implementation Notes

- Uses NumPy arrays and element-wise operations for high-performance coordinate-based texture synthesis.
- Implements spatial warping and logical displacement to create the illusion of folding surfaces and sharp digital tears.
- RGB channels are independently synthesized, shifted with `np.roll`, and composited back to produce intense chromatic aberration.
- Direct memory-buffer writing (`py5.np_pixels`) is used for rapid frame generation prior to ffmpeg compilation.

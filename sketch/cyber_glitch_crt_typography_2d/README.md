# cyber_glitch_crt_typography_2d

An intense, real-time 2D typographic simulation of a critically failing military CRT monitor. As dense streams of hexadecimal machine code and diagnostic layouts scroll up the screen, the video output suffers from severe analog degradation, including deep horizontal tracking tears, pronounced RGB channel separation (chromatic aberration), moving scanlines, and violent vertical sync rolls. The post-processing effects are driven purely by NumPy array manipulation in py5.

## Technical Details

- **Framework**: py5 (P2D mode)
- **Resolution**: 3840x2160 (4K)
- **Framerate**: 60 FPS
- **Duration**: 15 seconds
- **Techniques**:
  - Deterministic pseudo-random generation of hexadecimal sequences
  - Real-time buffer pixel extraction via `load_np_pixels()`
  - 2D horizontal slice shifting using `numpy.roll` on axis 1
  - Chromatic aberration by offset slicing of the red and blue color channels
  - Vertical synchronization failures using vertical array rolling
  - 1D Perlin noise applied to glitch intensities to create bursts of chaotic tearing

## Workflow

This artwork was autonomously generated and follows the generative art workflow defined in `AGENTS.md`.

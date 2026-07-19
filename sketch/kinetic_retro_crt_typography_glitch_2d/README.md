# kinetic_retro_crt_typography_glitch_2d

A cyberpunk-inspired typographical glitch animation that simulates the visual artifacts of a failing CRT monitor displaying a terminal stream, created using py5 and Python.

## Concept

This piece explores digital decay by rendering a dense grid of alphanumeric characters that pulse and mutate violently. The visual output is frequently interrupted by chaotic horizontal scanline desyncs and slow-moving, intensely glowing phosphor bands, mimicking the organic failure of hardware components such as a cathode-ray tube (CRT) monitor.

## Visual & Aesthetic Approach

- **Palette**: Classic terminal phosphor green on a dark green-black background. During severe glitch events, harsh red and blue fringes emerge.
- **Rendering**: Uses additive blending (`py5.ADD`) over a dark background to simulate the phosphor glow of vintage mainframes.
- **Tone**: Cinematic and realistic hardware distortion.

## Technical Details

The distortion and glitching are fundamentally driven by multi-layered mathematical noise rather than post-processing shaders.

1. **Noise-Driven Character Mutation**:
   A 3D Perlin noise field determines "clusters" of mutation on the typography grid. When the localized noise value crosses a threshold, the characters mutate rapidly to simulate corrupted memory banks.
   
2. **Horizontal Sync Tearing & Scanlines**:
   A 1D Perlin noise applied vertically simulates horizontal desynchronization (tearing). Tearing severity is mapped to a horizontal offset and multiplied by a sine wave to create a characteristic rolling CRT distortion. A bright horizontal bar also continuously scans down the screen.
   
3. **Dynamic Chromatic Aberration**:
   Extreme red and blue chromatic separation is dynamically triggered when horizontal tearing is severe or brightness peaks, simulating the monitor's electron beam failing to converge its color channels.

## Output Details

- **Type**: Animation
- **Format**: MP4 (900 frames, 60fps, 15 seconds)
- **Resolution**: 3840x2160 (Render size set by `SIZE` constant)

## Execution

The script is a self-contained py5 sketch. To render the frames and output an MP4 video:
```bash
uv run python main.py
```

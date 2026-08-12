# kinetic_sonoluminescence_cavitation

An animated 3D visualization of sonoluminescence and acoustic cavitation. Particles represent gas bubbles trapped, oscillating, and violently collapsing in an acoustic standing wave field.

## Details

- **Date**: 2026-08-11
- **Theme**: Sonoluminescence and acoustic cavitation. Bubbles are trapped in pressure nodes of a sound field, oscillating and collapsing to emit short bursts of light and shockwaves.
- **Technique**: Manual 3D rotation, perspective projection, depth-sorting (Painter's Algorithm), and depth-fading implemented in Python/NumPy, bypassing the OpenGL `P3D` renderer for headless server stability. Concentric projected rings represent acoustic fields, and bubble collapses trigger glowing hot-spots and expanding billboard-projected shockwave spheres.
- **Color Palette**:
  - Background: Deep indigo/violet (`#03010b`)
  - Dominant: Cobalt blue and deep purple (`#120e3c`, `#23277a`)
  - Accent: Vibrant electric cyan (`#00f0ff`) and hot-spot white (`#ffffff`)
- **Format**: Animation (60fps)

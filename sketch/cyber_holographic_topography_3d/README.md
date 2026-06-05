# cyber_holographic_topography_3d

## Details
- **Date**: 2026-06-03
- **Format**: Animation (15s @ 60fps)
- **Theme**: A high-tech, glowing holographic map of an alien topography. The terrain sweeps underneath the camera, glowing with neon scanlines and floating data-points.
- **Technique**: A 3D scrolling mesh generated via 2D Perlin noise that shifts continuously on the Y-axis to simulate forward movement over the landscape. The mesh is rendered using `py5.TRIANGLE_STRIP` with additive blending. The structure is drawn with glowing holographic cyan strokes and deep neon blue translucent fills, while high-elevation peaks trigger a warning red color change. Floating points of light follow the terrain surface.
- **Color palette**:
  - Background: Pitch Black
  - Dominant (60%): Holographic Cyan (lines)
  - Secondary (30%): Deep Neon Blue (surface fill)
  - Accent (10%): Warning Red (data points / high peaks)
  - Mood: cyberpunk / sci-fi

## Description
An animated 3D flight over a holographic data-terrain. The camera glides steadily forward over a shifting, procedural mountain range composed entirely of glowing neon wireframes and translucent blue data-surfaces. As peaks rise above a critical threshold, their wireframes flash into warning red. Ethereal data points float gently above the surface, completing the cybernetic, tactical-map aesthetic.

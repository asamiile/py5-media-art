# neon_synthwave_grid_terrain_3d

## Details
- **Date**: 2026-06-03
- **Format**: Animation (15s @ 60fps)
- **Theme**: A classic retro-futuristic synthwave landscape. An endless wireframe terrain scrolling towards the camera beneath a glowing digital sun.
- **Technique**: A 3D wireframe terrain is generated using `py5.TRIANGLE_STRIP`. The height mapping is driven by `py5.os_noise()` combined with a spatial mask to create a flat central valley surrounded by mountainous ridges. By offsetting the noise coordinates dynamically, the terrain appears to fly endlessly forward. The color of the wireframe shifts across a gradient based on depth. In the background, a massive sun is drawn with additive glowing layers and horizontal scanlines that animate upwards.
- **Color palette**:
  - Background: Very Dark Purple (5, 0, 15)
  - Dominant (60%): Hot Pink / Magenta (grid lines)
  - Secondary (30%): Cyan / Aqua (mountains / distant grid)
  - Accent (10%): Sunset Orange (the glowing sun)
  - Mood: retro / synthwave / cyber

## Description
An animated 3D love letter to the 1980s retro-futuristic aesthetic. An infinite, neon-lit wireframe terrain rushes towards the viewer, transitioning in color from deep cyan in the distance to hot magenta in the foreground. Towering digital mountains flank a smooth central valley, leading the eye toward the horizon. Looming above it all is a massive, glowing sunset-orange sun, sliced by animating horizontal scanlines that complete the iconic synthwave vibe.

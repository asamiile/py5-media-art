# chromatic_glitch_cube_field

## Metadata
- **Date**: 2026-05-23
- **Theme**: A digital glitch-art animation featuring a tumbling field of wireframe cubes distorted by intense, p
- **Technique**: Unknown
- **Logic Lab Reference**: 

## Concept
A digital glitch-art animation featuring a tumbling field of wireframe cubes distorted by intense, procedural chromatic aberration and CRT scanlines.

- **Date**: 2026-05-23
- **Theme**: Glitch art, chromatic aberration, retro-futurism, VHS distortion.
- **Technique**: Instead of slow pixel-by-pixel manipulation, this sketch achieves real-time chromatic aberration by rendering the entire 3D scene three times per frame—once for the Red channel, once for Green, and once for Blue. These passes are composited using `py5.BLEND_MODE(py5.ADD)`. Under normal conditions, the color channels are slightly offset on the X-axis, creating a rainbow edge-fringe. High-frequency 1D Perlin noise dictates a "glitch intensity" variable; when the noise spikes above a threshold, the color channels are violently and randomly displaced in 3D space, causing the white wireframes to shatter into vibrant RGB shadows. A semi-transparent black overlay provides retro CRT scanlines. 15s 60fps MP4.
- **Description**: A vast, dark void is filled with hundreds of tumbling, white wireframe cubes. Suddenly, the video signal appears to tear and glitch. The cubes violently split apart into pure red, green, and blue ghost-images before snapping back together. The camera slowly dollies forward through the field while the intense chromatic aberration and thick CRT scanlines give the piece a raw, analog-video aesthetic.

## Technical Details
- **Renderer**: Unknown
- **Simulation**: Unknown
- **Visuals**: Unknown
- **Animation**: Contains animation details

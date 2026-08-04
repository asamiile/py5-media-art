# kinetic_underwater_caustic_beams_2d

![Preview](kinetic_underwater_caustic_beams_2d_p1.png)

## Metadata
- **Date**: 2026-08-04
- **Theme**: Focused sunlight slicing through an undulating oceanic surface, creating shifting, luminous cathedral-like beams in a deep blue void.
- **Technique**: Numerical light ray refraction (Snell's law approximation) cast from an interfering multi-octave wave surface. Light rays are traced down through 80 depth layers to build a high-resolution caustic density field.
- **Logic Lab Reference**: `physics/caustic_light_field/caustic_light_field.py`

## Concept
This artwork captures the optical beauty of sunlight focusing through dynamic waves into the ocean abyss. The light rays bend as they pass through the wavy surface interface, converging to form shifting, web-like patterns of intense light (caustics) that slice through the deep blue column. Drifting organic dust particles and plankton act as passive light scatterers, glowing with warm amber golden light whenever they drift into the focused pathways of the volumetric caustic beams.

## Technical Details
- **Renderer**: P2D
- **Simulation**: Vectorized light ray propagation in NumPy. 1,500 rays are dynamically simulated at all 85 depth steps concurrently using array broadcasting and accumulated via `np.add.at`. Gentle underwater drift of 320 particles is simulated via 3D Perlin noise vector fields.
- **Visuals**: Realistic multi-octave water surface waves using overlapping harmonics, bilinear upscaling from a 640x360 simulation grid to a 3840x2160 (4K) viewport, and Tyndall scattering intensity calculations that scale particle glow size and core brightness.
- **Animation**: 15 seconds @ 60fps (900 frames) compiled via FFmpeg.

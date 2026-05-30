# bioluminescent_volumetric_beams

A generative digital media art animation depicting beams of soft, bioluminescent light piercing through a deep oceanic fog, illuminating a dense field of drifting micro-organisms.

## Artistic Theme

This work captures the quiet, nocturnal beauty of deep-sea marine snow and bioluminescence. Beams of light sweep slowly across the dark abyss, mimicking underwater sunbeams (crepuscular rays) refracted by ocean waves. The drifting spores and organic dust remain dim in the darkness, only flashing to life with vibrant, saturated glow when swept by the light cones. The motion is slow, peaceful, and fluid, representing the organic rhythm of oceanic life.

## Technique

- **Volumetric Crepuscular Rays**: Modulates the intensity and angle of multiple light shafts using sine-based oscillations and Perlin noise. The rays are drawn as fine radial lines with opacity envelopes to simulate dense scattering in water.
- **Vectorized Particle Illumination**: Tracks 1,200 particles under soft upward drift and curl-noise currents. Uses vectorized NumPy math to compute exact geometric intersections (distance and angular spread) with the light cones in real-time, mapping the peak illumination value to the particle's glow color and brightness.
- **Rendering & Composition**: Designed in HSB color mode and rendered at 4K (3840×2160) at 60fps with additive blending (`py5.ADD`) and short temporal trails for smooth motion blur.

## Running

Run the animation and compile the MP4 video using the `uv` toolchain:

```bash
uv run python sketch/bioluminescent_volumetric_beams/main.py
```

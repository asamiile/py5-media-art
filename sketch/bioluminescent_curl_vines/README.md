# bioluminescent_curl_vines

A generative digital media art animation depicting climbing vines and sprouting leaves guided by curl noise vector fields.

## Artistic Theme

This work captures the organic morphogenesis of climbing plants in a magical nocturnal environment. Multiple vine systems spawn at the forest floor and climb upwards, attracted horizontally to three invisible columns. Guided by the complex currents of curl noise, the vines twist, wrap, and branch as they grow, sprouting luminous, translucent leaves that pulse softly. The color transitions smoothly from deep emerald green to electric teal and radiant yellow-gold at the tips, leaving soft, additive light trails in the dark slate atmosphere.

## Technique

- **Column Attraction & Growth Bias**: Swarms of 340+ vine agents grow upwards under a constant vertical velocity bias, while being horizontally pulled towards three vertical coordinate targets to form column-like growth structures.
- **Curl Noise Vector Guidance**: Growth velocities are modulated by a 2D curl noise field computed via finite differences of Perlin noise.
- **Tapering & Sprouting**: The lines taper smoothly based on age, while HSB color values transition along the paths. Soft, double-ellipse leaves are sprouted periodically, aligned with the vine's heading angle.
- **Trails & Vignette**: Employs progressive background clears combined with additive blending (`py5.ADD`) to create smooth motion trails.
- **Render Output**: Renders at 4K resolution at 60fps with a 10-second duration.

## Running

Run the animation and compile the MP4 video using the `uv` toolchain:

```bash
uv run python sketch/bioluminescent_curl_vines/main.py
```

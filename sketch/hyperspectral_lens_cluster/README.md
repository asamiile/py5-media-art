# hyperspectral_lens_cluster

A 2D projection of complex gravitational lensing through a massive cluster of dark matter and galaxies.

## Description

A mesmerizing window into the deep universe; distant, colorful galaxies are stretched and warped into elegant, shimmering arcs and glowing Einstein rings by an invisible, massive cluster in the foreground, creating a spectral tapestry of light against the silent obsidian void.

## Technique

- **Gravitational Deflection**: Vectorized deflection model where background galaxy light paths are bent by a cluster of 6 massive foreground objects ($Mass \in [40k, 80k]$).
- **Hyperspectral Smearing**: Stylized chromatic aberration where RGB channels are deflected by different factors ($1.08x, 1.0x, 0.92x$) to simulate relativistic spectral effects.
- **Background Synthesis**: 60,000 particles organized into 50 distinct "galaxies" with randomized color temperatures.
- **Rendering**: Multi-pass additive blending (`py5.ADD`) to capture the high-intensity light buildup in lensed arcs.
- **Format**: 10-second animation @ 60fps, 4K resolution.

## Preview

![preview_p1](preview_p1.png)

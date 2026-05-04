# Synthetic Aurora

A digital reimagining of atmospheric phenomena. 

## Thematic Concept
'Synthetic Aurora' explores the intersection of natural beauty and digital glitch. It visualizes a future where the night sky is filled with algorithmic currents of light, shimmering with chromatic aberration and spectral interference.

## Technical Details
- **Noise-Driven Advection**: 15 layers of vertical Bezier curtains are deformed by multi-octave Perlin noise.
- **Chromatic Aberration**: Each curtain is split into R, G, and B components with spatial offsets, creating a prismatic "fringe" effect characteristic of high-end optical sensors.
- **Persistence Rendering**: Uses a low-alpha feedback loop to create smooth motion trails and a glowing, ethereal atmosphere.
- **Logic Lab Integration**: References `physics/additive_wave` for the interference-based shimmering and `physics/perlin_noise_walker_lines` for the organic movement.

## Logic Lab References
- `physics/additive_wave`
- `physics/perlin_noise_walker_lines`

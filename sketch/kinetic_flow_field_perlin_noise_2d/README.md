# kinetic_flow_field_perlin_noise_2d

## Concept
A massive generative flow field moving 500,000 glowing particles simultaneously. The particles are driven by a continuous 3D Perlin noise field, creating beautiful twisting currents, chaotic swirls, and elegant flowing rivers of light over time.

## Technique
Evaluating 3D Perlin noise individually for half a million points per frame in Python would be extremely slow. To achieve massive scale, a highly-optimized vectorized approach is used:
1. A coarse $120 \times 67$ grid of Perlin noise angles is generated.
2. `scipy.ndimage.zoom` instantly upscales that grid to a full $3840 \times 2160$ NumPy array using bilinear interpolation.
3. The 500,000 particles round their coordinates to map to this giant dense velocity field array. 
This trick allows the 500,000 particles to be updated 3 times per frame instantly.

## Palette
- **Trails**: Deep magenta, electric blue, and glowing purple, separated into batches.
- **Background**: Gently fading black (alpha 10) to create long glowing trails.
- **Blending**: `ADD` blend mode gives the intersecting particles a brilliantly luminous, fiery intensity.
- **Mood**: Fluid, electric, chaotic, luminous

## Format
Animation (450 frames @ 30fps)

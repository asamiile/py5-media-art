# kinetic_metaball_lava_lamp_2d

## Concept
A glowing neon lava lamp made of organic, merging 2D metaballs that slowly drift, combine, and separate.

## Technique
True metaball distance field calculation is utilized: `sum(R^2 / distance^2)`. Since calculating this for millions of pixels per frame is very heavy in Python, it's optimized by computing a 1/4th resolution grid (960x540) via NumPy vectorized broadcasting in real-time. This produces smooth neon color gradients based on the field thresholds. The generated image is instantly written to Py5 using `create_image_from_numpy()` and upscaled seamlessly via bilinear filtering to perfect 4K.

## Palette
- **Background**: Deep blue to dark purple gradient
- **Metaballs**: Bright neon pink and orange cores fading into cyan and magenta edges
- **Mood**: Hypnotic, organic, soothing, retro

## Format
Animation (450 frames @ 30fps)

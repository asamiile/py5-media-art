# kinetic_metaball_lava_lamp_2d

![Preview](kinetic_metaball_lava_lamp_2d_p1.png)

## Metadata
- **Date**: 2026-06-28
- **Theme**: A glowing neon lava lamp made of organic, merging 2D metaballs that slowly drift, combine, and separ
- **Technique**: True metaball distance field calculation is utilized: `sum(R^2 / distance^2)`. Since calculating this for millions of pixels per frame is very heavy in Python, it's optimized by computing a 1/4th resolution grid (960x540) via NumPy vectorized broadcasting in real-time. This produces smooth neon color gradients based on the field thresholds. The generated image is instantly written to Py5 using `create_image_from_numpy()` and upscaled seamlessly via bilinear filtering to perfect 4K.
- **Logic Lab Reference**: 

## Concept
A glowing neon lava lamp made of organic, merging 2D metaballs that slowly drift, combine, and separate.

## Technical Details
- **Renderer**: Unknown
- **Simulation**: Unknown
- **Visuals**: Unknown
- **Animation**: Contains animation details

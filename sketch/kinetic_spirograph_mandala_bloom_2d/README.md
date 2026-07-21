# kinetic_spirograph_mandala_bloom_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
A hyper-dense, glowing mandala constructed from overlapping layers of morphing spirograph curves. The rigid, mathematical geometry undulates and folds dynamically, creating the illusion of a massive, blooming, radioactive neon lotus flower.

## Techniques
- **Vectorized Hypotrochoids**: The core shapes are generated using exact parametric equations for hypotrochoids (the math behind spirographs). By evaluating 8000 vertices per layer using NumPy, the curves remain perfectly smooth and continuous.
- **Dynamic Morphing**: The three main parameters of the spirograph (the fixed circle radius $R$, the rolling circle radius $r$, and the pen distance $d$) are continuously modulated by overlapping sine waves. This causes the internal loops to collapse, expand, and bloom over time.
- **Layering and Rotation**: 12 distinct layers are drawn, scaling down exponentially towards the center. Each layer has a slight rotational offset, creating a deep, complex, tunnel-like vortex.

## Palette
Extremely bright, additive neon pinks, magentas, and electric blues. The additive blending causes the densest intersections of the lines to burn white-hot.

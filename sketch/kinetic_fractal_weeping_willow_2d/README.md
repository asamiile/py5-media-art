# kinetic_fractal_weeping_willow_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
A highly detailed, ethereal fractal tree swaying gently in an invisible, pulsing wind. The algorithm mimics a weeping willow, with branches progressively drooping downwards as the recursion deepens, creating a dense, glowing canopy.

## Techniques
- **Deep Recursion**: A classic recursive branching algorithm is pushed to a depth of 14, generating over 16,000 individual branch segments every single frame.
- **Noise-Driven Wind**: Instead of static angles, each branch's rotation is dynamically offset by an OpenSimplex noise value. The noise is sampled using the branch's depth and the current frame time (`py5.os_noise(depth * 0.5, time_offset)`), causing ripples of wind to naturally sweep up through the branches.
- **Droop Mechanics**: An additional downward rotational bias (`droop = depth * 0.05`) is added at each step, forcing the dense outer branches to curve downwards like a willow.
- **Additive Canopy**: `py5.ADD` blend mode ensures that where the thousands of tiny branches overlap, the color intensely accumulates into bright white/gold highlights.

## Palette
Ethereal green, gold, and white on a dark forest-green background.

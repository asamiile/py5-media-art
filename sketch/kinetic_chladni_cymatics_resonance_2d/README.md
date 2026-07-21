# kinetic_chladni_cymatics_resonance_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
A physics-inspired simulation of cymatics. 100,000 tiny "sand" particles dance on a virtual metal plate, settling into the nodal lines of complex acoustic resonant frequencies (Chladni patterns). As the frequencies shift smoothly over time, the sand organically re-organizes into new, intricate geometric shapes.

## Techniques
- **Chladni Nodal Math**: Uses the standard Chladni equation $C(x,y) = \sin(nx)\sin(my) - \cos(mx)\cos(ny)$. The zero-crossings of this function represent the nodes (areas of zero vibration).
- **Gradient Descent**: The particles are dynamically pushed away from high-vibration areas. This is achieved by computing the finite difference gradient of the squared Chladni function and moving particles down the gradient.
- **Brownian Excitation**: To prevent particles from getting permanently stuck when the nodal lines shift, a small amount of normally-distributed random noise is injected every frame, simulating the acoustic "bouncing" of the sand grains.

## Palette
A deep, dark navy/velvet background provides stark contrast for the thousands of metallic gold and bronze particles, which accumulate to form bright, glowing structures.

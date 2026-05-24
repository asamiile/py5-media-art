# strange_attractor_clifford_morph

A dynamic visualization of the 2D Clifford Strange Attractor smoothly morphing between different chaotic regimes.

- **Date**: 2026-05-23
- **Theme**: Chaos theory, strange attractors, dynamical systems.
- **Technique**: An ultra-fast vectorized Python simulation mapping 500,000 points through the Clifford attractor equations iteratively. Instead of static parameters, the variables $(a,b,c,d)$ are modulated by smooth sine waves over the 15-second duration, causing the fractal structure to seamlessly unfold, collapse, and transform. A dense 2D histogram (density map) is calculated each frame using `numpy.add.at` and mapped to a Cyberpunk-inspired Magenta, Blue, and Cyan additive palette directly in the pixel buffer. 15s 60fps MP4.
- **Description**: Millions of microscopic particles dance along invisible mathematical boundaries, tracing out impossibly intricate, folding shapes. As time progresses, the rules of the universe shift—causing the ghostly, neon-lit geometric web to warp and tear, constantly revealing new, mesmerizing symmetries hidden within the chaos.

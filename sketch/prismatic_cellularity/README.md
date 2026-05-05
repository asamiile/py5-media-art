# Prismatic Cellularity

A generative media art sketch exploring the intersection of urban metabolism and cellular logic through multi-scale Worley noise and spectral pressure.

## Concept

This work reimagines a futuristic metropolis as a living organism. Using a hybrid of Manhattan and Euclidean distance metrics, it generates a dense grid of "districts" that pulse and breathe. The sharp, iridescent edges represent high-pressure data conduits, while the glowing cores suggest the operational heart of each cellular block.

## Techniques

- **Hybrid Worley Noise**: Combines L1 (Manhattan) and L2 (Euclidean) distance metrics to balance architectural rigidity with organic growth.
- **Spectral Edge detection**: Luminous boundaries are extracted from the distance field (F2 - F1) and colored based on local strain and time-based harmonics.
- **Dynamic Lattice**: Feature points drift and oscillate, creating a continuous "breathing" effect across the city.
- **Atmospheric Depth**: A star-field background and bottom-up haze provide a sense of scale and nocturnal atmosphere.
- **Optimized Rendering**: Uses NumPy for high-performance distance field computation and cellular partitioning.

## Controls (during development)

- The sketch runs autonomously for 10 seconds to generate a high-quality animation.
- Previews are saved as `preview_p1.png`.
- Final animation is exported as `output.mp4`.

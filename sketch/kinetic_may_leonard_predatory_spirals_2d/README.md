# kinetic_may_leonard_predatory_spirals_2d

![Preview](kinetic_may_leonard_predatory_spirals_2d_p1.png)

## Metadata
- **Date**: 2026-08-17
- **Theme**: Three bioluminescent species locked in a cyclic, predatory dance, forming beautiful spirals and waves of dominance.
- **Technique**: Vectorized 2D numerical solver of the May-Leonard PDE equations in NumPy, species density color-blending, and a glowing Laplacian edge filter.

## Concept
This artwork explores biological competition and self-organization through the May-Leonard cyclic competition model (similar to a continuous rock-paper-scissors game). Three distinct species (rendered in vibrant magenta, cyan, and amber) compete for space: magenta consumes cyan, cyan consumes amber, and amber consumes magenta. As they chase and overtake each other, they form massive, rotating spiral wave fronts. A custom Laplacian edge detector adds a sharp, bright white glow to the active predator-prey frontiers.

## Technical Details
- **Renderer**: Py5 default (updated pixel buffer directly)
- **Simulation**: Explicit finite-difference solver for May-Leonard PDEs in NumPy with sub-stepping (3 steps/frame).
- **Visuals**: Multihue species blending, and squared Laplacian boundary edge outline highlights.
- **Animation**: 15s @ 60fps

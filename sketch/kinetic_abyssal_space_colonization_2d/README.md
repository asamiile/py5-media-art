# kinetic_abyssal_space_colonization_2d

![Preview](kinetic_abyssal_space_colonization_2d_p1.png)

## Metadata
- **Date**: 2026-08-06
- **Theme**: Vascular growth, space colonization, deep sea mycelium, bioluminescent networks
- **Technique**: Space Colonization algorithm, dynamic pipe-model branch thickness calculation (descendant count back-propagation), dual-pass glowing vector lines, HSB depth-based color gradients (warm gold to electric teal), technical HUD telemetry.

## Concept
A 4K kinetic visualization of an organic mycelial network colonizing an active auxin attractor field in the deep ocean abyss. Using the Space Colonization algorithm, branch tips compete for nutrients (scattered glowing points). Once branch tips get close enough to a nutrient, it is absorbed and disappears, directing subsequent growth to remaining frontiers.

To create a realistic, organic wood-like structure, branch thickness is dynamically calculated based on the number of descendant nodes (representing the volume of traffic/flow through each limb). Branch colors shift from warm glowing amber at the root trunk to electric cyan and teal at the growing tips.

## Technical Details
- **Renderer**: Java2D
- **Simulation**: Space Colonization with 800 scattered attractors and dynamic node branch lists. Grouped numpy calculations process vector directions fast enough to handle multiple simulation steps per frame.
- **Visuals**: HSB abyssal color scheme, descendant-weighted dual-pass glow line rendering, vignette framing, and telemetry readout HUD.
- **Animation**: 15 seconds @ 60 FPS (900 frames)

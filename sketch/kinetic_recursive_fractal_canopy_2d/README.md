# kinetic_recursive_fractal_canopy_2d

## Concept
An elegant, glowing forest of fractal trees. The branches of these fractal trees dynamically sway and blow as if interacting with a gentle, organic wind passing through the canopy.

## Technique
Instead of an L-System grammar generator, pure programmatic recursion (`draw_branch()`) combined with py5's robust `push_matrix()` and `pop_matrix()` transformation stack is used. A central tree is drawn at recursive depth 13 ($2^{13} = 8,192$ branches), and two background trees are drawn at depth 11 ($2,048$ branches each). To simulate the organic swaying of the wind, the branching angles are continuously modulated by a 2D Perlin noise field evaluated with `py5.noise(time, depth)`. This makes the thinner outer branches sway heavily while the thick trunks stay rooted.

## Palette
- **Forest**: The tree branches smoothly fade their color mapping as depth increases, transitioning from a deep pink/purple at the base of the trunk to a brilliant, glowing cyan at the outer tips. 
- **Atmosphere**: A subtle motion blur (`blend_mode(BLEND)` with high alpha overlay) makes the canopy glow.
- **Mood**: Elegant, kinetic, organic, magical

## Format
Animation (450 frames @ 30fps)

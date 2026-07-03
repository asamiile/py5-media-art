# kinetic_physics_cloth_simulation_wind_2d

A physics-based simulation of a massive sheet of cloth blowing in an invisible, turbulent wind. The fabric bends, folds, and ripples dynamically.

## Techniques

Verlet integration for rigid distance constraints applied across a 60x40 grid of interconnected points. The wind force is driven by Perlin noise, pushing the cloth organically while the top edge remains partially pinned.

## Palette

"Shimmering Silk": The fabric color shifts from deep purple and cyan to bright magenta based on the velocity of each section, contrasted against a warm, muted copper background.

# Generative Voronoi Shatter

An animated 15s sequence of a fracturing geometric field.

## Concept

- **Theme**: A geometric field fracturing into a Voronoi diagram that dynamically shifts over time.
- **Technique**: Uses `scipy.spatial.Voronoi` applied to an array of points that wander using Perlin noise. The cells are rendered with additive blending, and the stroke weight of the fracture edges depends on their distance to the center.
- **Palette**: Dark monochromatic void with neon pink glowing fracture edges.

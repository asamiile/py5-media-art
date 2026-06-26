# generative_isometric_labyrinth_2d

## Theme
A shifting, Escher-like maze of isometric columns that rise and fall based on 3D noise patterns.

## Technique
Uses standard 2D vector drawing to simulate a 3D isometric projection, completely bypassing OpenGL/P3D engine. Sorts blocks back-to-front based on grid iteration. Color and column height are driven by OpenSimplex noise parameterized by time.

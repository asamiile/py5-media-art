# kinetic_quadtree_subdivision_2d

**Date**: 2026-07-21
**Type**: Animation (900 frames, 60fps)

## Concept
A kinetic homage to the Bauhaus and De Stijl movements (like the works of Piet Mondrian). It uses a QuadTree algorithm to recursively subdivide space into rectangles, creating a rigid geometric composition that is constantly being shattered and reformed by an invisible, fluid noise field.

## Techniques
- **Recursive Subdivision**: The canvas is split into a QuadTree. The function recursively calls itself up to 7 layers deep (`MAX_DEPTH = 7`).
- **Noise-Driven Density**: Instead of dividing uniformly, each cell checks the value of a 3D OpenSimplex noise field (`py5.os_noise`) at its center. If the noise exceeds a depth-dependent threshold, the cell splits into four. This causes areas of the canvas to become hyper-detailed while others remain massive, solid blocks.
- **Procedural Motifs**: Leaf nodes don't just fill with solid color; they are drawn with a padding to create distinct "blocks". Depending on the depth and noise, some cells procedurally generate internal geometric motifs (black circles, horizontal/vertical bars), adding to the architectural feel.
- **Infinite Panning**: The entire grid translates diagonally over time, creating a sense of continuous motion, while the noise field causes the cells to morph as they move.

## Palette
A strict Bauhaus palette: Off-white, Deep black, Crimson Red, Cobalt Blue, and Golden Yellow.

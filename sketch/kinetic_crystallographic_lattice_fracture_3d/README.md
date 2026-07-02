# Kinetic Crystallographic Lattice Fracture 3D

## Concept
This sketch explores the simulation of a highly dense, semi-stable crystalline lattice undergoing catastrophic fracture points. Using purely generative point structures, it projects a 3D field of vertices into a 2D canvas, using an optical depth approach to simulate distance. As spherical waves of instability pass through the lattice, points displace violently outwards, glowing with bright magenta energy, contrasting against the stable glowing cyan structure.

## Technical Implementation
- Pure Python 2D projection from a synthetic 3D dataset.
- 100,000 discrete points clustered around a uniform grid lattice structure.
- Mask-based point categorization to selectively color vertices and alter stroke weights efficiently using NumPy indexing.
- ADD blend mode over a dark void background to build an accumulated neon exposure.

## Execution
- `N_points`: 100,000
- `FPS`: 60
- `Duration`: 15 Seconds
- `Resolution`: 3840x2160

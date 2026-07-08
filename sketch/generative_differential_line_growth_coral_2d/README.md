# generative_differential_line_growth_coral_2d

**Date**: 2026-07-07
**Type**: Animation (10-30s @ 60fps)

## Concept
A generative simulation of differential line growth, inspired by the organic growth patterns of coral, brain tissue, and nudibranch frills. A closed loop of nodes continually expands and self-organizes. As the line grows, it begins to buckle and fold into intricate organic shapes.

## Techniques
The physics engine is implemented using vectorized NumPy operations. It balances three forces on a closed polygon of up to 4500 nodes:
1. **Repulsion**: Nodes push each other apart when they get too close (simulated via an $O(N^2)$ distance matrix).
2. **Attraction**: Adjacent nodes in the loop pull together like springs.
3. **Growth**: When the distance between two adjacent nodes exceeds a threshold, a new node is dynamically inserted into the array.
The simulation is incredibly fast thanks to `numpy.float32` matrix broadcasting.

## Palette
Bioluminescent ocean. Deep blue-black background, with the coral line glowing in neon coral pinks, warm oranges, and seafoam greens. Colors are dynamically mapped using `py5.remap` based on the node's index along the loop and time.

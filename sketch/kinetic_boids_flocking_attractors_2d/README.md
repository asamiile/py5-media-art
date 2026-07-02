# Kinetic Boids Flocking Attractors 2D

## Concept
A massive swarm of luminous, bird-like particles following complex emergent behavior (Boids algorithm) around moving gravitational attractors, painting glowing trails in the void.

## Technical Implementation
- 2,500 boids simulated in numpy at 60 frames per second.
- Uses `scipy.spatial.KDTree` to efficiently find spatial neighbors, enabling large-scale Separation, Alignment, and Cohesion forces calculation.
- Two orbital attractors introduce gravitational pull that disrupts the flock and sends them into swirling vortexes.
- Rendered with an additive blend over a low-alpha rect background to create beautiful, long-fading neon motion trails using `py5.lines()` from old to new positions.

## Execution
- `Boids`: 2,500
- `FPS`: 60
- `Duration`: 15 Seconds
- `Resolution`: 3840x2160

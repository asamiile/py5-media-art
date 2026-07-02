# Kinetic Cybernetic Neural Network Activation 3D

## Concept
A massive 3D brain-like network of artificial neurons firing in cascading sequence, representing synthetic thought. The sketch creates a complex web of interwoven nodes and edges that gently rotate in 3D space, while a volumetric wave of energy propagates through the connections, igniting paths with brilliant neon electricity.

## Technical Implementation
- Network generation using 2000 normally-distributed 3D points.
- Edge calculation optimized using `scipy.spatial.KDTree` to connect nodes within a proximity threshold.
- Custom isometric/perspective matrix projection handling 3D-to-2D coordinates without py5's P3D engine.
- A volumetric sine wave field determines activation thresholds for nodes and edges dynamically.
- Additive blending (`py5.ADD`) used to stack the glowing opacities of hundreds of concurrent intersecting lines.

## Execution
- `Nodes`: 2000
- `Edges`: ~15,000+ dynamically calculated lines
- `FPS`: 60
- `Duration`: 15 Seconds
- `Resolution`: 3840x2160

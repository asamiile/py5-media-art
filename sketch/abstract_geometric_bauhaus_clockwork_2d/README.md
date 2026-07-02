# Abstract Geometric Bauhaus Clockwork 2D

## Concept
A complex array of rigid geometric shapes (circles, semi-circles, thick lines, and arcs) colored in a classic Bauhaus palette (Red, Blue, Yellow, Black, Off-White) that interlock and rotate like a massive, abstract clockwork mechanism.

## Technical Implementation
- Constructed using a hierarchical tree of rotating "Gear" nodes, up to a depth of 4.
- Drawing uses standard `py5.push_matrix()`, `py5.rotate()`, and `py5.translate()` to calculate relative child geometry dynamically.
- Each node picks a primitive shape at random (circle, semi-circle, arc, or cross) and assigns itself a gear speed based on a pseudo-gear ratio calculation relative to its parent radius to ensure meshing speeds.
- Uses a fixed `np.random.seed()` so the mechanical layout stays consistent across the frames while the time-based rotation sweeps through dynamically.

## Execution
- `Format`: Vector rendering using classic 2D matrix transformations.
- `FPS`: 60
- `Duration`: 15 Seconds
- `Resolution`: 3840x2160

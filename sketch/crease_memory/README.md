# crease_memory

A dark sheet remembers pressure as luminous geometric relief.

## Concept

The work treats folds as memory: every crease becomes a stored force, visible only where light catches the material and exposes the history of pressure.

## Technique

- **Signed Crease Fields**: Random fold lines are represented as signed distances and accumulated with `tanh` transitions to form a continuous heightfield.
- **Short Secondary Folds**: Localized creases interrupt the dominant directions so the surface feels handled rather than mechanically tiled.
- **Normal-Based Shading**: The generated heightfield is converted to surface normals and lit from one direction to reveal low-relief structure.
- **Stress Highlights**: Thin copper and teal accents trace the highest-pressure fold ridges.

## Visual Impression

A near-black folded surface fills the frame, with quiet graphite planes broken by teal edges, mauve shadows, and copper stress lines.

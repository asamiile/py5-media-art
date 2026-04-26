# dla_lightning

**Theme**: "Branching discharge" — a single lightning bolt as a fractal branching structure, evoking electrical discharge, river deltas, and neuronal dendrites

**Technique**: Midpoint displacement fractal with stochastic side branching, numpy pixel accumulation, log-scale tone mapping

**Description**: A main channel from sky to ground is recursively subdivided: each segment's midpoint is displaced perpendicular to the segment, with displacement scaling as `length × roughness^depth`. At each split, a side branch spawns with probability proportional to depth. Segments are rendered via gaussian glow accumulation into a float canvas, then tone-mapped with log1p. Depth encodes color — near-white cyan core → dim steel blue at the finest tips.

**Palette**:
- Background: `#020308` near-black
- Core trunk: `#d2f0ff` cold near-white
- Mid branches: `#3ca0f0` electric blue
- Fine tips: `#123c78` dark steel blue

**Preview**: `preview.png`

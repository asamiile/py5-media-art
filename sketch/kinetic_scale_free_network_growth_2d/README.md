# kinetic_scale_free_network_growth_2d

**Date**: 2026-07-31  
**Type**: Animation (1200 frames, 60fps)  

## Concept

A 4K kinetic visualization of the **Barabási-Albert preferential attachment model**, illustrating the self-similar growth and emergence of a scale-free network topology. Set against a deep cosmic obsidian void, the network initiates from a tiny circular core and grows as new nodes arrive, connecting preferentially to nodes with higher degrees. The physical arrangement resolves dynamically in real time via a spring force-directed layout. The resulting topology blooms like a breathing galactic stellar network, with massive glowing star-like hubs dominating the core structure while delicate chains of leaf nodes stretch out into the darkness.

## Techniques

- **Barabási-Albert preferential attachment growth**:
  New nodes arrive and link to $M_{attach} = 3$ existing nodes. The attachment probability $P(i)$ for node $i$ is proportional to its current degree $k_i$:
  $$P(i) = \frac{k_i}{\sum_j k_j}$$
  This creates a power-law degree distribution where a few major hubs dominate the topology.

- **Vectorized Fruchterman-Reingold Force Layout**:
  Pairs of nodes interact via repulsive forces ($F_{rep} = K_{rep} / d^2$) calculated in parallel using NumPy broadcasting. Connected nodes are pulled together by attractive spring forces ($F_{att} = K_{att} \cdot d$). A damping factor of $0.85$ per frame keeps the physics stable.

- **Exponentially Smoothed Viewport Scaling**:
  To prevent scale jittering or jerking when new nodes attach at a distance, a low-pass filter (exponential moving average with factor $0.05$) is applied to both the network's center coordinates and its bounding-box span, yielding smooth transitions.

- **Concentric Glow Bloom & Color Spectrum Mapping**:
  Node degrees are mapped to a color gradient: Leaf nodes (degree 1-2) glow in Glacial Cyan (`#00e5ff`), transitioning through structural Electric Violet (`#b356ff`), up to dominating hubs that glow in Radiant Magenta (`#ff2a85`). Concentric transparent layers combined with a Perlin noise loop create organic shimmering effects on the stars.

- **Persistent Motion Trails**:
  A translucent wipe (`alpha = 20` out of 255) maintains a fading visual history of the layout's evolution, highlighting the orbital paths of nodes as they settle into place.

## Palette

- **Background**: Obsidian Space Void (`#05060b`).
- **Hub Nodes**: Radiant Magenta (`#ff2a85`).
- **Core Edges / Mid-Degree Nodes**: Electric Violet (`#b356ff`).
- **Leaf Nodes / Faded Edges**: Glacial Cyan (`#00e5ff`).

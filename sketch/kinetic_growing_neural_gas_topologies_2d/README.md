# kinetic_growing_neural_gas_topologies_2d

**Date**: 2026-07-31  
**Type**: Animation (1200 frames, 60fps)  

## Concept

A 4K kinetic visualization of Fritzke's unsupervised competitive learning algorithm — **Growing Neural Gas (GNG)** — adapting its topology to dynamic multi-center attractor fields. Set against a deep obsidian night sky, three moving spatial signal sources (a Lissajous orbiter, a shifting counter-orbiter, and a breathing radial ring) project signals into a 2D space. The neural gas competitive network advects and grows, spawning new nodes in high-reconstruction-error regions while pruning aged, inactive edges. The visual representation creates a fluid, self-organizing organic web that stretches, grows, and decays, reminiscent of bioluminescent neural synapses or cosmic filament clusters chasing invisible energy currents.

## Techniques

- **Fritzke's Growing Neural Gas competitive advection**:
  For each step, a signal is drawn from the dynamic spatial mixture. The two closest nodes (winner $B_1$ and runner-up $B_2$) are identified. $B_1$ and its topological neighbors are advected towards the signal:
  $$\Delta v_{B_1} = \epsilon_b (S - v_{B_1})$$
  $$\Delta v_{N} = \epsilon_n (S - v_{N})$$
  Accumulating error at the winner guides localized node splits.

- **Dynamic Node Splitting & Edge Pruning**:
  Every $\lambda = 40$ steps, a new node is inserted at the midpoint between the node with the highest accumulated error and its worst neighbor. Edges increment in age and are pruned when they exceed $a_{max} = 80$, causing isolated nodes to be deleted and network topologies to split.

- **Proportional Coordinates & Centered 16:9 Mapping**:
  To prevent stretching on the widescreen 4K canvas ($3840 \times 2160$), coordinates in the normalized range $[0.05, 0.95]^2$ are mapped using a centered $1:1$ ratio:
  $$x_{screen} = \frac{W}{2} + (x - 0.5) H$$
  $$y_{screen} = y H$$

- **Glow Bloom & Color Interpolation**:
  Edges fade in thickness and color from glowing Electric Cyan (`#00e5ff`) to deep Midnight Indigo (`#25305c`) as their topological age increases. Nodes are drawn with double circles (a solid core and a wide low-opacity bloom) transitioning from Cyan (low local error) to bright Solar Gold (`#ffd54f`, high adaptation error).

- **Persistent Motion Trails**:
  A translucent overlay blend (`alpha = 16` out of 255) is applied each frame instead of a clean background wipe. This preserves history, rendering smooth glowing advection trails as the network elements drift.

## Palette

- **Background**: Obsidian Void (`#05070c`).
- **Young Edges / Stable Nodes**: Electric Cyan (`#00e5ff`).
- **Aging Edges / Inactive Nodes**: Deep Midnight Indigo (`#25305c`).
- **High-Error / Active Adaptation Nodes**: Solar Gold (`#ffd54f`).

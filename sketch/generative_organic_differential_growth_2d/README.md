# generative_organic_differential_growth_2d

A generative visualization of Differential Growth, simulating the biological process of a single closed loop expanding into complex brain-coral / fingerprint patterns.

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
This sketch simulates the physical expansion of a continuous membrane. A closed loop of nodes is subjected to two opposing forces: adjacent nodes act as springs pulling each other together (Attraction), while all nearby nodes repel each other (Repulsion). When a segment stretches beyond a threshold, it divides via mitosis, injecting a new node into the array.
To make this computationally feasible for thousands of nodes at 60 FPS, the spatial repulsion queries are heavily optimized using `scipy.spatial.cKDTree`, reducing the time complexity from $O(N^2)$ to $O(N \log N)$. The resulting organic line meanders and folds into itself, producing striking, naturalistic textures resembling coral reefs or brain tissue.

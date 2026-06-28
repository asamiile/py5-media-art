# generative_differential_line_growth_2d

## Concept
A continuous differential line growth algorithm simulating biological cellular expansion, slowly blooming into intricate, brain-like or fingerprint-like patterns.

## Technique
Differential line growth requires applying local repulsion forces while maintaining segment connectivity and handling dynamic subdivision as segments grow too long. This becomes computationally expensive $O(N^2)$ and generally destroys rendering speeds with thousands of nodes. To optimize this, the algorithm uses a pure Python/NumPy integration of `scipy.spatial.KDTree` to rapidly query local spatial neighborhoods in underlying C/C++ every frame. This allows the organic form to efficiently subdivide and grow into thousands of nodes without bottlenecking the real-time Py5 loop.

## Palette
- **Background**: Faint trailing dark purple/black
- **Line**: Glowing bright orange/gold
- **Mood**: Organic, biological, mesmerizing, expanding

## Format
Animation (450 frames @ 30fps)

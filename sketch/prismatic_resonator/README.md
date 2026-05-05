# prismatic_resonator

A generative animation exploring the concept of optical physics, spectral refraction, and geometric resonance.

## Concept
The work visualizes the behavior of light rays as they bounce and refract inside a set of nested geometric resonators. Using a recursive ray-tracing algorithm, the piece creates complex, shimmering patterns of spectral light. The chromatic dispersion and high-persistence path accumulation suggest an underlying optical harmony in a star-dusted night sky.

## Technique
- **Recursive Ray-Tracing (P2D)**: Simulating the behavior of light rays bouncing inside a circular resonator using reflection physics.
- **Chromatic Dispersion Simulation**: Splitting each ray into three constituent spectral components (Electric Cyan, Cobalt, Royal Amethyst) with slightly different refraction/reflection angles.
- **High-Persistence Path Accumulation**: Using a persistence buffer with additive blending (`py5.ADD`) to build up complex, silken patterns of light over time.
- **Atmospheric Starfield**: A high-density starfield reinforces the cosmic/astronomical context, addressing the "beautiful night sky" request.

## Palette
- **Rays**: Electric Cyan, Cobalt Blue, Royal Amethyst
- **Fading Trails**: Spectral Indigo, Deep Violet
- **Void**: Midnight Blue/Black

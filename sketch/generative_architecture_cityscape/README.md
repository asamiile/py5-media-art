# generative_architecture_cityscape

A procedurally generated, infinite cyberpunk city stretching into the digital horizon.

- **Date**: 2026-05-23
- **Theme**: Procedural architecture, 3D cityscapes, cyberpunk, neon lighting.
- **Technique**: Utilizes pure 3D rendering (`py5.box`, `py5.camera`) to build an infinite grid of city blocks. The height of each building is determined by 2D Perlin noise multiplied by a "downtown factor," ensuring taller skyscrapers cluster near the central avenue while shorter buildings spread into the suburbs. The camera constantly pushes forward down the central avenue, dynamically spawning and culling buildings to maintain performance. Dual directional lighting combined with glowing HSB strokes gives the city a distinct neon-drenched, retro-futuristic aesthetic. 15s 60fps MP4.
- **Description**: The camera glides steadily down a wide, empty avenue surrounded by hundreds of towering skyscrapers. The city stretches to the horizon in a dark void. Each building is cast in dark shadows but strongly outlined with brilliant, shifting neon light. As you fly forward, the skyline endlessly generates itself, rising and falling organically like a concrete mountain range.

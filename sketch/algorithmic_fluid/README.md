# algorithmic_fluid

A generative animation exploring the concept of digital liquid, spectral flow, and viscous light.

## Concept
The work visualizes a shimmering, viscous flow of spectral light that swirls and mixes in a deep cosmic void. Using a grid-based fluid simulation, the piece creates complex, organic flow patterns. Spectral dyes are injected into the fluid, shifting in color based on local velocity magnitude, suggesting an underlying fluid harmony under a star-dusted night sky.

## Technique
- **Grid-Based Fluid Simulation (P2D)**: A simplified Navies-Stokes simulation (density and velocity advection) on a 100x100 grid, using NumPy for efficient state updates.
- **Spectral Dye Advection**: Injecting spectral dyes into the fluid that shift in color from Electric Cyan to Royal Amethyst based on local velocity magnitude.
- **Luminous Persistence Rendering**: Using a high-persistence buffer with additive blending (`py5.ADD`) to create silken, flowing textures over time.
- **Atmospheric Starfield**: A high-density starfield reinforces the cosmic/astronomical context, addressing the "beautiful night sky" request.

## Palette
- **Flowing Dyes**: Electric Cyan, Royal Amethyst, Molten Gold
- **Fading Trails**: Deep Indigo, Violet
- **Void**: Midnight Blue/Black

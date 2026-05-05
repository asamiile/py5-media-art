# spectral_coral

A generative animation of synthetic marine life, exploring the concept of metabolic light and crystalline growth.

## Concept
The work visualizes "spectral coral" structures that grow and pulse in a dark, star-dusted void. Using a stochastic branching algorithm, the piece creates intricate, fractal-like structures that shimmer with rhythmic light. Pulses of spectral light travel along the branches, suggesting an underlying metabolic process in a silent, high-tech abyss.

## Technique
- **Stochastic Branching Growth**: A recursive growth algorithm that builds intricate, fractal-like "coral" structures using randomized lengths and angles.
- **Metabolic Light Pulse**: Animate pulses of spectral light that travel along the branches from the root to the tips, mapping the pulse intensity to HSB spectral colors.
- **Spectral Bloom Rendering**: The branches and pulses are rendered using additive blending (`py5.ADD`) to create a glowing, iridescent texture.
- **Atmospheric Starfield**: A high-density starfield reinforces the cosmic/underwater-like scale, addressing the "beautiful night sky" request.

## Palette
- **Coral Structure**: Dark Slate/Graphite (#323246)
- **Metabolic Pulses**: Electric Cyan, Cyber Lime, Royal Amethyst
- **Void**: Midnight Blue/Black

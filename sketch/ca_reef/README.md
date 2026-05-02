# ca_reef

A generative artwork simulating the growth and calcification of a biological coral reef using multi-state cellular automata.

## Concept
The piece explores the emergent complexity of biological systems. It visualizes a living grid where "polyps" grow, age, and eventually calcify into permanent rocky structures, mimicking the eons-long process of reef building.

## Technique
- **Multi-State Cellular Automata**: A custom 6-state CA model governs the life cycle of the reef, from initial growth to stable calcification.
- **Organic Polyp Rendering**: Each cell renders a unique organic form using radial noise and state-dependent scaling, breaking the rigid grid structure.
- **Jittered Composition**: Noise-based coordinate jittering ensures that the reef has a natural, non-mechanical layout.
- **Calcification Logic**: States that reach the maximum age are rendered as permanent, rocky structures in sandy tones, providing a structural anchor to the vibrant living polyps.
- **Underwater Atmosphere**: A multi-layered background featuring noise-driven "water shimmer" and a sandy "bottom" texture creates an immersive marine environment.
- **Shadow & Depth Pass**: Subtle shadows are applied to each polyp to create a sense of three-dimensional volume and overlap.

## Metadata
- **Date**: 2026-05-02
- **Theme**: cellular automata, biology, self-organization, coral
- **Technique**: multi-state CA, organic rendering, noise-based jitter, atmospheric depth pass

# gravitational_echoes

An abstract generative animation capturing the rhythmic distortion of spacetime during a binary black hole merger.

## Concept
The work visualizes "gravitational waves" as they ripple outward from two orbiting massive bodies. As the objects approach their final "merger," the frequency of the waves increases and the orbital radius shrinks (the "chirp" signal). This creates a complex, interference-rich tapestry of light that bends the background stars and pulses with cosmic resonance.

## Technique
- **Binary Merger Simulation**: Two emitters follow a non-linear "chirp" orbit where $f \propto t^2$ and $r \propto (1-t^{1.5})$.
- **Interference Fringes**: Concentric wave-fronts from both emitters are rendered using additive blending (`py5.ADD`), creating bright "nodes" where crests overlap.
- **Metric Distortion**: A high-density starfield (1200 stars) is dynamically warped using the phase of the local gravitational wave, simulating the stretching and squeezing of spacetime.
- **Spectral Palette**: Electric Cyan and Royal Amethyst ripples pulse against a deep indigo-obsidian void, culminating in a white-gold "merger" flash.

## Palette
- **Background**: Obsidian Indigo (#020205)
- **Waves**: Electric Cyan, Royal Amethyst
- **Focal Point**: White-Gold merger core

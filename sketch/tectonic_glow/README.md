# tectonic_glow

A generative animation exploring the concept of planetary stress and the emergence of molten energy from crustal fractures.

## Concept
The work simulates a "tectonic" surface where shifting plates create immense subterranean pressure. As the nodes drift and collide, the connections between them are subjected to varying levels of stress. These "seismic" tensions are visualized as glowing, molten cracks that pulse with the energy of the planet's core.

## Technique
- **Dynamic Stress Mesh**: A particle system where nodes drift via Perlin noise. Connections are dynamically calculated based on proximity.
- **Spectral Fractures**: Connections are rendered as quadratic Bezier curves with midpoint displacement to simulate the jagged, irregular nature of geological cracks.
- **Stress-Weighted Emission**: The color and weight of each crack are mapped to its local tension, shifting from deep violet (low stress) to electric magenta and molten gold (high stress).
- **Planetary Atmosphere**: A dark sienna-charcoal background combined with a high-density starfield reinforces the cosmic/planetary scale.

## Palette
- **Crust**: Deep Earth Sienna/Charcoal (#0a0505)
- **Cracks**: Molten Gold, Electric Magenta, Deep Violet
- **Nodes**: Flickering Orange/Red hotspots

# kinetic_swarm_vortex_milling_2d

An animated 2D active matter simulation based on the Couzin three-zone swarming model, visualizing the spontaneous emergence of coherent swirling mills and collective vortex motion.

## Concept & Visuals
The simulation models collective self-propelled particle behavior:
- **Repulsion Zone** prevents close-range collisions, keeping the agents separated.
- **Orientation Zone** aligns velocities with neighboring agents, promoting collective motion.
- **Attraction Zone** draws agents towards the centroid of local neighbors, maintaining swarm cohesion.
- Over time, the parameters dynamically cycle, forcing the swarm to transition between disorganized swarming, parallel flocking, and circular vortex milling states.
- Particles are colored based on their velocity vector direction on an HSB color wheel, leaving long, glowing, overlapping trails.
- A high-DPI native 4K HUD overlay monitors real-time order parameters: polar order (flocking consensus) and angular momentum (vortex mill strength), plotted on dynamic history graphs.

## Technical Implementation
- Fully vectorized NumPy distance matrix calculations and zone masks updated at 60 FPS.
- Soft circular containment potential confining agents inside a boundary ring.
- Frame-to-frame trail persistence created via low-opacity background blending combined with additive color blending.

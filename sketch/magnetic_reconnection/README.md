# magnetic_reconnection

An intricate visualization of solar magnetic physics and plasma energy dynamics.

## Concept

This work simulates the phenomenon of magnetic reconnection, where magnetic field lines from different domains suddenly "snap" and re-route, releasing immense amounts of kinetic energy. This process is visualized as high-tension magnetic filaments that pulse with energy in a deep, star-dusted void.

## Technique

- **Vectorized Particle Advection**: 50,000 particles are advected along a multi-pole magnetic field using NumPy for high performance.
- **Dynamic Field Topology**: The magnetic dipoles are periodically modulated to force "reconnection" events, changing the flow patterns and accelerating local particles.
- **Spectral Energy Mapping**: Particle colors shift from deep blue/teal to intense white-gold based on the local magnetic field intensity (a proxy for kinetic energy).
- **Persistence Trails**: A slow-fade background creates silken, thread-like filaments that trace the history of the magnetic field lines.
- **High-Density Starfield**: A procedurally generated background provides a sense of cosmic scale and depth.

## Palette

- **Deep Indigo**: The vacuum of space.
- **Electric Cobalt / Teal**: Low-energy magnetic filaments.
- **Rose-Gold / Molten Gold**: High-energy reconnection sites.
- **Stark White**: Peak energy acceleration.

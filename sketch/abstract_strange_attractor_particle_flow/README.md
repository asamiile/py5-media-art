# abstract_strange_attractor_particle_flow

## Metadata
- **Date**: 2026-05-23
- **Theme**: A massive 3D particle simulation visualizing the chaotic dynamics of the Lorenz Strange Attractor
- **Technique**: Unknown
- **Logic Lab Reference**: 

## Concept
A massive 3D particle simulation visualizing the chaotic dynamics of the Lorenz Strange Attractor.

- **Date**: 2026-05-23
- **Theme**: Chaos theory, strange attractors, Lorenz system, butterfly effect, fluid dynamics, particle swarm.
- **Technique**: Leverages NumPy array vectorization to compute the differential equations for the classic Lorenz attractor ($dx, dy, dz$) on 50,000 independent particles simultaneously at 60fps. The particles are initialized in a tiny cluster and are quickly ripped apart by the chaotic vector field, splitting into two distinct orbiting lobes (the "butterfly wings"). A subtle oscillating noise field is added to the equations, giving the mathematically rigid attractor a more organic, fluid-like wind distortion. The scene is rendered using `py5.POINTS` with additive blending and motion blur. Particle colors dynamically map from cyan to magenta based on their instantaneous velocity. 15s 60fps MP4.
- **Description**: 50,000 glowing particles are caught in an invisible, chaotic gravitational storm. Starting as a dense singularity, the swarm is violently stretched and torn into two swirling, interconnected rings resembling the wings of a butterfly. The glowing dust races along the complex mathematical curves of the Lorenz attractor, leaving brilliant trails of cyan and magenta light that continuously fold in on themselves. As the camera slowly rotates, the infinite, non-repeating complexity of chaos theory is revealed as a beautiful, breathing cosmic nebula.

## Technical Details
- **Renderer**: Unknown
- **Simulation**: Unknown
- **Visuals**: Unknown
- **Animation**: Contains animation details

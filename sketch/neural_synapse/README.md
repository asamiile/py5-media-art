# neural_synapse

An abstract visualization of complex signal propagation within a bioluminescent neural network, capturing the chaotic yet structured firing patterns of a synthetic mind.

## Concept
This work models a graph-based network of 180 "neurons" connected by stochastic synapses. It explores the emergence of cascading activation patterns (neural storms) and the dynamic nature of information flow across an intricate, three-dimensional lattice.

## Technique
- **Stochastic Graph Simulation**: A network of 180 nodes in 3D space with connections based on proximity.
- **3D Rotation & Projection**: The entire network undergoes a slow dual-axis rotation, projected onto a 2D plane with perspective scaling.
- **Signal Cascade Engine**: Signals are triggered periodically and propagate through the network, branching at nodes based on a threshold/cooldown model.
- **Dynamic Trails**: Signals leave short-lived, additive glow trails using line-segment buffers.
- **Bioluminescent Bloom**: Activated nodes exhibit multi-layered additive blending and halo effects, with intensities tied to their current activation level.

## Files
- `main.py`: The network simulation and rendering code.
- `output.mp4`: A 5-second 60fps animation of the neural activity.
- `preview.png`: A snapshot of the cascading signals.

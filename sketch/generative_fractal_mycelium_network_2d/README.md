# generative_fractal_mycelium_network_2d

An organic, branching mycelium network that grows across the screen, mimicking fungal hyphae exploring for nutrients.

## Details

- **Type**: 2D animation
- **Length**: 10 seconds (60fps)

## Technique

A progressive branching algorithm (similar to L-systems but continuous) where active tips grow forward, wander slightly, and probabilistically split into multiple new branches. The canvas is not cleared each frame, allowing the network to permanently etch itself into the dark earthy background.

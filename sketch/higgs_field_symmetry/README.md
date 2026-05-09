# Higgs Field Symmetry Breaking

A high-fidelity 3D visualization of the Higgs mechanism and spontaneous symmetry breaking in the early universe.

## Concept

This artwork simulates a 3D scalar field $\phi$ undergoing a phase transition. In the early high-energy phase, the field oscillates around the zero-state (symmetric vacuum). As the universe cools, the potential shifts into a "Mexican Hat" shape, causing the field to roll down into a new, non-zero vacuum manifold (the "gutter" of the potential).

## Technical Details

- **Simulation**: 200,000 particles representing local field excitations.
- **Physics**: Implements a Langevin-like second-order evolution driven by the gradient of the Higgs potential $V(\phi) = \alpha |\phi|^2 + \beta |\phi|^4$.
- **Transition**: The $\alpha$ parameter shifts from positive to negative, triggering the spontaneous symmetry breaking.
- **Rendering**: Multi-pass additive point rendering in P3D with a spectral palette (White/Violet to Cyan/Gold).
- **Environment**: 4K/60fps high-bitrate animation with a dense background starfield (12,000 stars).

## Aesthetics

The visual narrative follows the transition from chaotic high-energy white-violet fluctuations into a structured, shimmering "condensate" of cyan and gold light, representing the birth of mass in the cosmos.

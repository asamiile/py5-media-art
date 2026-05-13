# synaptic_nebula

![Preview](preview_p1.png)

## Metadata
- **Date**: 2026-05-06
- **Theme**: Cosmic biology, information flow, synaptic currents, beautiful night sky.
- **Technique**: Physics-driven particle simulation (80,000 particles) using NumPy. Particles gravitate toward 30 "synaptic nodes" while being perturbed by noise-driven drift. Vectorized rendering using `py5.points()` for performance. Synaptic nodes feature pulsing multi-pass glow coronas (spheres) with distance-based scaling. HSB palette (Cyan/Blue/Violet/Rose). 60fps high-bitrate MP4.
- **Logic Lab Reference**: None

## Concept
A vast, bioluminescent neural network in the deep void; 80,000 data-particles flow through nebular filaments, connecting 30 pulsing synaptic nodes that flare with the light of a cosmic intelligence.

## Technical Details
- **Renderer**: P3D
- **Simulation**: NumPy, particle.
- **Visuals**: HSB spectral mapping, bloom-like highlights, prismatic color, dark-field contrast.
- **Animation**: 10 seconds at 60fps

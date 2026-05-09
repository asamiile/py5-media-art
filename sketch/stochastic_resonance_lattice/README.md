# stochastic_resonance_lattice

A majestic visualization of synchronization through noise in a 3D lattice of coupled oscillators.

## Description

A shimmering cloud of electric cyan and deep amethyst light pulses with a hidden rhythm. In the double-well landscape of their internal states, thousands of virtual oscillators are buffeted by cosmic noise and a faint periodic signal. Through the mechanism of stochastic resonance, the chaos suddenly gives way to a synchronized geometric lattice, pulsing with neon white energy as the collective transitions between states against the star-dusted indigo night.

## Technique

- **Physics**: 3D simulation of 150,000 particles following Langevin dynamics in a double-well potential ($V(x) = -x^2/2 + x^4/4$).
- **Dynamics**: Nonlinear synchronization driven by a combination of Gaussian white noise and a periodic forcing signal (stochastic resonance).
- **Rendering**: Multi-pass additive point rendering with state-dependent HSB coloring.
- **Palette**: Electric Cyan, Deep Amethyst, and Neon White.

## Metadata

- **Date**: 2026-05-09
- **Format**: Animation (20s @ 60fps)
- **Resolution**: 1920x1080 (Preview)
- **Tools**: py5, NumPy, FFmpeg

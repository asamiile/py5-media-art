# polymer_chain_langevin_dynamics

Microscopic polymer chains floating in a heat bath, folding and unfolding randomly under thermal noise and a swirling fluid field.

## Technical Details

- **Type**: Animation (15s @ 60fps)
- **Algorithm**: 2D Langevin dynamics simulation of 150 polymer chains, each consisting of 1,000 particles (150,000 total). Particles are connected by Hookean springs, subject to random Gaussian thermal kicks and a macro-scale harmonic swirl field. Simulated with vectorized NumPy physics across 5 substeps per frame.
- **Rendering**: Multi-pass additive point rendering using `py5.points` with a "Cyan to Magenta" HSB palette against a very dark, motion-blurred background to simulate the fluorescent glow of tagged DNA or polymers in a microfluidic channel.

## Preview

![Preview](polymer_chain_langevin_dynamics_p1.png)

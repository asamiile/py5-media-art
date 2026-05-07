# kilonova_merger_ripple

A 3D simulation of a neutron star merger, capturing the binary inspiral, gravitational wave ripples, and the subsequent kilonova explosion.

## Description

A violent and beautiful celestial event; two tiny, blinding dots dance in a tightening spiral, warping the very stars behind them, before vanishing into a spectacular explosion of shimmering gold and platinum dust that fills the void in a complex, toroidal and polar jet structure.

## Technique

- **Binary Dynamics**: Simulation of two neutron stars spiraling inward with a decay-rate model, increasing in frequency as they approach collision at frame 240.
- **Space-time Distortion**: Real-time background starfield ripple effect, where the amplitude and frequency are coupled to the binary orbital parameters.
- **Kilonova Physics**: Post-collision ejection of 300,000 particles using a dual-mode distribution (toroidal disk + relativistic polar jets).
- **Nucleosynthesis Color Mapping**: Spectral shift from blinding blue-white (stars) to rose gold and platinum (heavy element ejecta) via time-dependent lerping.
- **Rendering**: 3D particle simulation with additive blending and a fading central fireball.
- **Format**: 10-second animation @ 60fps, 4K resolution.

## Preview

![preview_p1](preview_p1.png)

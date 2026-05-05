# stellar_equilibrium

A visualization of the precarious balance within a massive star — gravitational collapse vs. magnetic tension.

## Description

`stellar_equilibrium` captures the majestic and violent life of a star. At the center, a dense core pulses with nuclear fusion, casting a warm amber glow that ripples through the surrounding vacuum. Thousands of plasma agents are held in orbit by a complex interplay of forces: the relentless inward pull of gravity and the outward push of magnetic pressure. Golden solar prominences (magnetic loops) surge from the core, while the entire system "breathes" in a rhythmic cycle of expansion and contraction against a deep, star-dusted night.

## Technical Details

- **Physics Engine**: N-body simulation with custom gravitational and magnetic force fields.
- **Magnetic Loops**: Dynamic Bezier paths driven by agent history and local tension gradients.
- **Rendering**:
    - Retina-aware pixel buffer accumulation for "long-exposure" plasma trails.
    - Noise-driven core luminosity with multi-layered Gaussian glow.
    - Stochastic starfield with atmospheric twinkling.
- **Palette**: `Stellar Night` — Solar Amber, Plasma Violet, Electric Magenta, Vacuum Indigo.

## Logic Lab Reference

- `physics/n_body_orbital_simulation/n_body_orbital_simulation.py` — gravitational logic.
- `physics/spring_connection/spring_connection.py` — tension and restoring force logic.

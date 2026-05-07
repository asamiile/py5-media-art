# tidal_disruption

A star's violent and beautiful death; caught in the immense gravity of a supermassive black hole, it is shredded into a glowing "noodle" of plasma that spirals toward the event horizon.

## Details

- **Theme**: Cosmic catastrophe, spaghettification, event horizon, beautiful night sky
- **Technique**: 3D particle simulation (180,000 particles) using a relativistic gravitational potential. A central "singularity" exerts non-linear tidal forces that stretch a spherical particle emitter into a long, twisting filament. Particles are colored by speed-based HSB (simulating Doppler shift and heating), with a multi-pass additive core glow for the photon ring.
- **Palette**: Deep indigo, electric cyan, molten orange, white-gold.
- **Format**: 60fps high-bitrate MP4.

## Technical Notes

- Uses NumPy for vectorized physics calculations.
- Implements a simplified relativistic correction to Newton's gravity to enhance the tidal shredding effect.
- Multi-pass sphere rendering for the central singularity's glow.
- Renders 180,000 points using `py5.POINTS` for high-density visual fidelity.

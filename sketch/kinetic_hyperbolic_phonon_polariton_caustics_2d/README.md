# kinetic_hyperbolic_phonon_polariton_caustics_2d

2D nanophotonics and condensed matter physics simulation depicting anisotropic polariton propagation, directional ray caustics, and sub-diffraction wavepacket canalization in a biaxial van der Waals crystal ($\alpha\text{-MoO}_3$) across the Reststrahlen band.

## Concept & Physics

In natural hyperbolic materials such as alpha-phase molybdenum trioxide ($\alpha\text{-MoO}_3$), the real components of the in-plane dielectric permittivity tensor possess opposite signs ($\text{Re}(\epsilon_x) \cdot \text{Re}(\epsilon_y) < 0$) within the mid-infrared Reststrahlen bands. Consequently, equifrequency surfaces in momentum space transform from closed circles or ellipses into open hyperbolas. 

When launched from nanoscale gold antenna tips, phonon polaritons propagate along open hyperbolic dispersion surfaces as hyper-confined, diffraction-free directional ray caustics with:
1. **Directional Ray Caustics**: Polariton energy flows strictly along asymptote angles $\theta_c(t) = \arctan\sqrt{|\epsilon_y / \epsilon_x|}$, forming macroscopic X-shaped diamond caustics.
2. **Negative Dispersion & Concave Wavefronts**: Sub-wavelength phase ripples ($\lambda_p \sim \lambda_0 / 100$) exhibiting concave inward curvature characteristic of negative phase velocity.
3. **Moiré Interference Networks**: Overlapping caustics from satellite antennas creating high-contrast standing wave moiré diamonds.
4. **Crystal Cleavage Step Terraces**: Reflections and standing-wave fringe localization at atomic step edges.
5. **Lagrangian Polariton Quasiparticles**: 4,000 hybrid phonon-polariton wavepackets streaming along Poynting vector rays.

## Aesthetics & Color Palette

- **Basal van der Waals Plane**: Midnight Obsidian Slate & Bismuth Indigo (`#090e1a` to `#1a162b`)
- **Hyperbolic Ray Caustics**: Phosphorescent Electric Emerald & Glacial Cyan (`#00ffaa`, `#00dcff`)
- **Interference Fringes & Moiré Nodes**: Neon Laser Fuchsia / Magenta & Amethyst Violet (`#ff0088`, `#8b00ff`)
- **Nano-Antenna Launch Pads**: Incandescent Solar Gold & Liquid Diamond White (`#ffdd00`, `#ffffff`)
- **Crystal Step Terrace Reflectors**: Luminescent Pale Cyan & Mint White (`#ccffff`)

## Specifications

- **Format**: Seamless looping animation (900 frames @ 60 FPS, 15 seconds)
- **Resolution**: 1920×1080 (HD preview) / 3840×2160 (4K master)
- **Engine**: py5 (Python Processing) + NumPy vectorized field synthesis + Blinn-Phong dual-light specular normal mapping

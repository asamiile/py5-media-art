# kinetic_non_hermitian_exceptional_point_caustics_2d

2D non-Hermitian wave physics and singular photonics simulation depicting parity-time (PT) symmetric coupled optical waveguides with balanced gain ($+i\gamma$) and loss ($-i\gamma$), dynamic parameter encircling through an Exceptional Point (EP, $\gamma = \kappa$), two-sheeted Riemann surface branch cut caustics, and non-reciprocal chiral photon amplification.

## Concept & Physics

In non-Hermitian open quantum and optical systems described by non-conservative Hamiltonians $H = \begin{pmatrix} \omega_0 + i\gamma & \kappa \\ \kappa & \omega_0 - i\gamma \end{pmatrix}$, spatial symmetry ($P$) and time-reversal symmetry ($T$) can remain intact even with energy dissipation:
1. **PT-Symmetric Phase vs. Broken Phase**: When gain/loss rate $\gamma < \kappa$, eigenvalues remain purely real ($\lambda_\pm = \omega_0 \pm \sqrt{\kappa^2 - \gamma^2}$), resulting in stable oscillatory Rabi flopping between waveguides. When $\gamma > \kappa$, eigenvalues become complex conjugate pairs, driving exponential runaway gain.
2. **Exceptional Point (EP) Degeneracy**: At the critical bifurcation point $\gamma = \kappa$, the square root discriminant vanishes. Unlike Hermitian diabolical points, both eigenvalues and eigenvectors coalesce into a single defective state.
3. **Riemann Surface Branch Cut Caustics**: Encircling the EP in parameter space reveals a two-sheeted complex Riemann surface. Crossing the branch cut induces chiral mode conversion and asymmetric energy transfer.
4. **Photonic Dielectric Normal Shading**: Dual-light Blinn-Phong specular relief visually sculpts the active gain and dissipative loss channels.
5. **Lagrangian Chiral Quasiparticles**: 2,400 photon rays navigate the coupled system, undergoing resonant tunneling that breaks into unidirectional amplification at the exceptional point bottleneck.

## Aesthetics & Color Palette

- **Photonic Dielectric Substrate**: Deep Obsidian Glass Void (`#03050c`)
- **Active Gain Channel**: Blinding Incandescent Neon Coral & Molten Solar Amber (`#ff5722`, `#ffb300`)
- **Dissipative Loss Channel**: Cryogenic Midnight Indigo & Actinic Amethyst (`#1e1b4b`, `#7c3aed`)
- **Exceptional Point Singularities**: Radiant Glacial Cyan & Electric Jade (`#00f5d4`, `#06b6d4`)
- **Coalescence Nodes**: Diamond Liquid Pearl White (`#ffffff`)

## Specifications

- **Format**: Seamless looping animation (720 frames @ 60 FPS, 12 seconds)
- **Resolution**: 1920×1080 (HD preview) / 3840×2160 (4K master)
- **Engine**: py5 (Python Processing) + NumPy vectorized 2x2 non-Hermitian Hamiltonian tensor synthesis + Riemann branch cut caustic mapping + Blinn-Phong specular relief + vectorized batch trail rendering (`py5.lines()`, `py5.points()`)

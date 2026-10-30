# kinetic_higher_order_topological_corner_states_2d

2D acoustic metamaterial and higher-order topological insulator (HOTI) simulation depicting a 2D Benalcazar-Bernevig-Hughes (BBH) quadrupole lattice, bulk bandgap insulation, gapped 1D perimeter edges, and robust zero-dimensional topological corner bound state condensation under resonant acoustic excitation.

## Concept & Physics

In standard topological insulators, a $d$-dimensional bulk hosts $(d-1)$-dimensional boundary states. In **higher-order topological insulators (HOTIs)**, a $d$-dimensional system hosts boundary states of dimension $(d-2)$ or lower:
1. **Benalcazar-Bernevig-Hughes (BBH) Quadrupole Model**: A finite rectangular 2D square lattice of coupled acoustic micro-resonators with staggered intra-cell and inter-cell coupling links ($\gamma, \lambda$) and synthetic $\pi$-flux per plaquette realizes a quantized bulk quadrupole moment $q_{xy} = e/2$.
2. **Gapped Bulk & Edge Hierarchy**: Both the 2D interior bulk and the 1D perimeter edge channels exhibit finite energy bandgaps, preventing acoustic transport through conventional propagation modes.
3. **Zero-Dimensional Corner Bound States**: At the four outer corners of the metamaterial plate ($d - 2 = 0$), mid-gap zero-energy topological states $\psi_k(x, y)$ emerge with exponential spatial localization into the bulk and alternating quadrupolar phase signs $(+1, -1, +1, -1)$.
4. **Resonant Acoustic Condensation**: Under dynamic acoustic frequency pumping, bulk scattering interference rapidly cancels out, channeling mechanical energy into four incandescent, indestructible corner resonance traps.
5. **Lagrangian Phonon Kinematics**: 2,200 acoustic phonon quasiparticles stream along subtle sub-lattice waveguides before becoming captured into tight topological vortex limit cycles around the four blazing corners.

## Aesthetics & Color Palette

- **Silicon Metamaterial Substrate Void**: Deep Obsidian Space Void (`#05070f`)
- **Micro-Pillar Resonator Lattice**: Midnight Cobalt & Slate Grid Mesh (`#0f172a` to `#1e293b`)
- **Topological Acoustic Pressure Waves**: Radiant Electric Mint & Glacial Cyan (`#06b6d4`)
- **Anti-Resonant Phase Shearing**: Cryogenic Indigo & Royal Violet (`#6366f1` to `#a855f7`)
- **Zero-Dimensional Corner Singularities**: Blinding Incandescent Solar Topaz & Liquid Pearl White (`#ffb703` to `#fffdf5`)
- **Phonon Quasiparticle Sparks & Streamlines**: Electric Mint Cyan & Radiant Topaz Gold

## Specifications

- **Format**: Seamless looping animation (720 frames @ 60 FPS, 12 seconds)
- **Resolution**: 1920×1080 (HD preview) / 3840×2160 (4K master)
- **Engine**: py5 (Python Processing) + NumPy vectorized BBH quadrupole field tensor synthesis + dual-light Blinn-Phong specular relief normal mapping + vectorized batch trail rendering (`py5.lines()`, `py5.points()`)

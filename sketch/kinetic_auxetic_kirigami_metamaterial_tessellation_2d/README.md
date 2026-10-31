# kinetic_auxetic_kirigami_metamaterial_tessellation_2d

Kinetic rotating rigid unit auxetic metamaterial tessellation executed in py5.

## Concept

Inspired by traditional Japanese *kirigami* (切り紙) papercraft, *sashiko* (刺し子) geometric stitching, and modern mechanical metamaterial physics (Grima & Evans rotating squares mechanism). A continuous sheet of rigid washi paper square facets expands and contracts through synchronized counter-rotating diamond hinge dynamics.

As the facets rotate, the negative Poisson's ratio causes the entire lattice to contract isotropically while opening rhythmic diamond-shaped voids, revealing an illuminated substrate of molten cinnabar and imperial gold leaf.

## Technical Details

- **Resolution**: 3840×2160 (4K UHD)
- **Duration**: 720 frames @ 60 FPS (12.0s seamless $C^1$ loop)
- **Mechanism**:
  - Center spacing: $D(t) = 2h \cos(\theta(t))$ along lattice vectors $\vec{u} = D(t) \cdot (1, 1)$ and $\vec{v} = D(t) \cdot (1, -1)$.
  - Alternating rotation: $\phi_{u, v}(t) = (-1)^{u+v} \theta(t)$.
  - Harmonic loop: $\theta(t) = \frac{\theta_{\max}}{2} (1 - \cos(2\pi t / T))$ with $\theta_{\max} = 38.0^\circ$.
- **Materiality & Multi-Layer Depth**:
  1. Base Ground: Obsidian slate (`#0e1016`).
  2. Substrate Glow: Radiant amber (`#d97706`), cinnabar (`#dc2626`), and imperial gold (`#f59e0b`) pulsing synchronously with facet aperture.
  3. Cast Shadows: 2-stage soft directional drop shadows and inter-facet ambient occlusion.
  4. Facets: Alternating Echizen mulberry bone white (`#fbf9f4`) and unbleached flaxen washi (`#f4ede2`).
  5. Relief: Dual debossed bevel grooves and fine geometric inlays.
  6. Pivots: Burnished gold leaf rivets at corner hinges and central faceted studs.
- **Anonymity**: 100% autonomous algorithmic generative art without human authorship marks, signatures, or name seals.

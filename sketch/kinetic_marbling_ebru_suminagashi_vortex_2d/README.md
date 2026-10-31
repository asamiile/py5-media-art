# kinetic_marbling_ebru_suminagashi_vortex_2d

Kinetic Ebru marbling and Suminagashi fluid shear dynamics simulation executed in py5.

## Concept

An artistic exploration of traditional Turkish Ebru (*ebru sanatı*) and Japanese Suminagashi (墨流し, "floating ink") paper marbling fluid dynamics, combining historical hydrodynamics with modern computational geometry.

In classical Ebru, insoluble mineral pigments (ground lapis lazuli, madder lake, ochre, malachite) suspended with ox gall float upon a viscous carragheen moss sizing bath. A fine wire comb (*tarak*) is drawn orthogonally across the bath to produce undulating *Gelgit* (tidal) chevron waves, while delicate stylus swirling imparts logarithmic core vortices. The artwork simulates 46 multi-tier concentric mineral pigment ribbons undulating under bidirectional comb shearing, viscous core vortex twisting, drifting gold foil (*kinpaku*) flecks, and an archival basin calibration graticule across warm torinoko washi vellum.

## Technical Details

- **Resolution**: 3840×2160 (4K UHD)
- **Duration**: 720 frames @ 60 FPS (12.0s seamless $C^1$ loop)
- **Genre Taxonomy**: Atmospheric / Painterly / Color Field
- **Fluid Mechanics & Kinematics**:
  - Multi-tier pigment bands: 46 concentric rings sampled at 220 radial coordinates rendered as continuous `QUAD_STRIP` gouache washes with delicate boundary contour lines.
  - Gelgit comb rake shearing: Harmonic spatial-phase displacement along orthogonal axes ($A_x \sin(\omega t + k_x x) \cos(\omega t/2 + \phi_r)$) simulating the viscous combing of carragheen sizing.
  - Viscous core vortex: Exponentially decaying shear swirl ($\theta(r) = \theta_0 e^{-r/r_0} \sin(\omega t)$) twisting the central droplet nucleus.
  - Floating gold leaf (*kinpaku*): 200 irregular 5-point polygonal gold foil flakes drifting gently across the bath surface tension.
- **Pigment & Materiality**:
  - Ground: Warm Torinoko washi vellum (`#f6f0e4`) with subtle laid paper chain-lines and archival basin borders (`#826950`).
  - Traditional Inks: Prussian indigo (*Ai* `#163058`), madder carmine (*Beni* `#b92d3e`), turmeric gold (*Kihada* `#dca22a`), shōen sumi black (`#14181e`), malachite celadon (*Rokushō* `#26737a`), and violet logwood (*Murasaki* `#824476`).
  - Specular Accents: Irregular gold foil (*kinpaku* `#ebc037`) with burnt ochre boundary relief.
  - Instrumentation: Ebru comb calibration millimeter rule and rotating stylus rake compass.
- **Anonymity**: 100% autonomous algorithmic generative art without human authorship marks, signatures, or name seals.

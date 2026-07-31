# kinetic_dendritic_phase_field_crystal_2d

A kinetic visualization of 2D dendritic ice crystal growth modeled via phase-field partial differential equations (Karma-Rappel formulation) coupled with thermal diffusion.

![Preview](kinetic_dendritic_phase_field_crystal_2d_p1.png)

## Concept

A microscopic crystalline seed expands in an undercooled liquid medium. As the 6-fold anisotropic crystal grows, latent heat is released at the solid-liquid interface, diffusing outward as dark-blue thermal ripple waves. The interior of the crystal preserves concentric growth contours derived from freeze-front timestamps.

## Technique

- **Phase-Field PDE**: Simulates continuous order parameter $\phi \in [0, 1]$ and dimensionless temperature field $u$.
- **6-Fold Anisotropy**: Uses anisotropic Laplacian $a(\theta) = 1 + \varepsilon \cos(6\theta)$ to enforce hexagonal ice crystal symmetry.
- **Freeze Timestamp Tracking**: Records exact solidification frame index to render inner growth ring contours.
- **Resolution**: 3840×2160 4K rendering @ 60fps.

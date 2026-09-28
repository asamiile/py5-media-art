# kinetic_dendritic_solidification_2d

A 2D kinetic simulation of non-equilibrium dendritic crystal solidification, Mullins-Sekerka morphological instability, and polarized light birefringence in an undercooled liquid melt.

## Concept & Physics

When a pure supercooled liquid or metallic alloy freezes into a crystalline solid, the smooth solidification interface becomes unstable to microscopic perturbations—a phenomenon described by the Mullins-Sekerka instability.

Latent heat of fusion rejected at the solid-liquid interface diffuses into the supercooled melt. Peaks in the interface project into regions of higher thermal undercooling $\Delta T = T_m - T_\infty$, increasing the local heat dissipation and accelerating tip growth into parabolic Ivantsov needles:
$$P_e = \frac{v_{tip} \rho_{tip}}{2 D_T}$$

This work captures:
1. **Mullins-Sekerka Side-Branching**: Competitive growth of primary dendritic needle trunks, secondary orthogonal side-branches, and tertiary micro-facets emerging from capillary thermal fluctuations.
2. **Crystallographic Anisotropy**: Multi-seed competitive growth combining 6-fold hexagonal symmetry (ice/hcp crystal lattices) and 4-fold cubic symmetry (fcc/bcc metal alloys) rotating in the melt.
3. **Thermal Diffusion & Convection Fields**: Isothermal latent heat envelopes and buoyant convection eddies circulating in the undercooled liquid melt.
4. **Crossed Nicol Birefringence Optics**: Optical retardation fringes $\Delta = (n_e - n_o) d$ revealing Michel-Lévy interference colors (peacock electric cyan, magenta, and solar gold) determined by the local crystallographic director $\theta(x, y)$.
5. **Specular Chrome / Liquid Metal Normal Mapping**: Dual-light Blinn-Phong specular shading creating liquid mercury / polished silver metallic facet depth.
6. **Lagrangian Solute Segregation Impurities**: 600 solute tracer particles pushed ahead of advancing dendritic tips, mapping concentration gradients and grain-boundary segregation ribbons.

## Color Palette

- **Dendritic Needle Spines & Cores**: Peacock Electric Cyan (`#00f0ff`) & Luminous Aquamarine (`#32ffb4`)
- **Birefringent Retardation Fringes**: Neon Fuchsia (`#ff00a0`) & Amethyst Violet (`#b432ff`)
- **Latent Heat Thermal Isotherms & Solute Impurities**: Incandescent Solar Gold (`#ffbe28`) & Amber Glow (`#ffaa20`)
- **Specular Facet Highlights**: Diamond White (`#ffffff`) & Liquid Silver Platinum
- **Undercooled Liquid Melt Abyss**: Deep Midnight Titanium Black (`#060812`)

## Technical Details

- **Resolution**: 1920×1080 (3840×2160 on Retina)
- **Frame Rate**: 60 fps
- **Duration**: 900 frames (15.0 seconds seamless loop)
- **Libraries**: py5, NumPy, subprocess (ffmpeg)

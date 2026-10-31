# kinetic_hamilton_conical_refraction_diabolical_points_2d

Autonomous generative media art animation simulating physical wave optics, Hamilton's 1832 prediction of conical refraction, and diabolical point singularities in biaxial anisotropic crystals (Aragonite $\text{CaCO}_3$) in 4K UHD 60fps (12.0s seamless loop).

## Concept

In 1832, Sir William Rowan Hamilton mathematically deduced from Augustin-Jean Fresnel's wave surface equations that when unpolarized light propagates along an optical axis in an anisotropic biaxial crystal, the light does not split into two discrete rays as ordinary double refraction dictates. Instead, because the two sheets of the Fresnel wave surface meet at four conical points—termed **diabolical points** or conical singularities—the light unfolds into a hollow cone of light. Upon exiting the crystal face, this cone resolves into two concentric bright rings separated by a profound dark circle: the famous **Poggendorff dark ring**.

This artwork translates the physical geometry of conical refraction, geometric Berry phase, and wave caustic topology into dynamic computational optics on an optical bench obsidian ground:

1. **Dual Concentric Poggendorff Rings & Caustic Interference**:
   - An inner emerald ($532\text{ nm}$ Nd:YAG) ring and an outer cyan coherent ring separated by an analytical dark null circle (radius $R_0 = 540\text{px}$).
   - 720 radial caustic rays modulated by Malus' law and Bessel diffraction fringes ($J_0$ and $J_1$) expanding and contracting in 12.0s harmonic resonance.
2. **Polarization Vector Needle Array & Geometric Berry Phase**:
   - 72 dual-arm orientation needles positioned along the Poggendorff ring illustrating the electric field vector orientation $\alpha = \theta / 2$.
   - A full $360^\circ$ traversal around the ring rotates the linear polarization by exactly $180^\circ$, demonstrating that diametrically opposed points possess mutually orthogonal polarizations.
3. **Rotating Wollaston Analyzer Extinction Lobes**:
   - As a linear polarizer rotates at frequency $\omega$, the transmitted intensity manifests as sweeping two-lobed crescent crescents of light with glowing caustic cusps that rotate around the perimeter at angular frequency $2\omega$.
4. **3D Intersecting Fresnel Wave Sheets**:
   - A 32-spoke double cone intersecting at the central diabolical singular apex, rotating in 3D stereographic perspective.
5. **Four-Corner Optical Bench Apparatuses**:
   - **Top-Left**: Biaxial crystal optical indicatrix ellipsoid with principal axes ($n_x = 1.530, n_y = 1.681, n_z = 1.686$) and optic axis intersections.
   - **Top-Right**: Poincaré polarization sphere projection tracking the cumulative $2\pi$ Berry phase trajectory.
   - **Bottom-Left**: Axial beam profile showing the double cone unfolding from the focal waist.
   - **Bottom-Right**: Wollaston analyzer extinction compass tracking the instantaneous extinction angle $\gamma(t)$.

## Technical Specifications

- **Resolution**: 3840 × 2160 (4K UHD)
- **Framerate**: 60 fps
- **Duration**: 720 frames (12.0s seamless loop)
- **Loop Mathematics**: All angular velocities $\omega_i = k_i \cdot \frac{2\pi}{T}$ with integer multipliers, guaranteeing mathematical identity between frame 0 and frame 720.
- **Color Palette**:
  - Optical Bench Deep Obsidian (`#07080e`)
  - Coherent Nd:YAG Laser Emerald & Electric Jade (`#10b981` / `#34d399` / `#059669`)
  - Optical Polarization Cyan & Cobalt (`#06b6d4` / `#38bdf8` / `#1d4ed8`)
  - He-Ne Crystalline Crimson & Amber Caustic Spikes (`#f43f5e` / `#fbbf24`)
  - Singular Optical Apex White (`#ffffff`)
- **Strict Anonymity**: 100% autonomous algorithmic generative art without human authorship marks, artist signatures, monograms, initials, or personal seals.

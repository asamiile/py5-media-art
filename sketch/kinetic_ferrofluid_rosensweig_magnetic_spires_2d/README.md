# kinetic_ferrofluid_rosensweig_magnetic_spires_2d

Kinetic ferrofluid Rosensweig instability and magnetic flux field simulation executed in py5.

## Concept

An artistic exploration of magnetic fluid dynamics, specifically the normal-field Rosensweig instability. When a colloidal suspension of ferromagnetic nanoparticles is subjected to a critical vertical magnetic threshold, the liquid surface spontaneously organizes into an ordered hexagonal lattice of sharp conical spires.

Under a dynamically rotating and modulating electromagnetic quadrupole field, the spires undulate in a chiral traveling wave. Each spire exhibits 3D conical geometry with metallic Blinn-Phong specular highlights, multi-ring capillary meniscus depressions, and glowing electric-cyan apical field concentration nodes, encircled by magnetic potential flux lines.

## Technical Details

- **Resolution**: 3840×2160 (4K UHD)
- **Duration**: 720 frames @ 60 FPS (12.0s seamless $C^1$ loop)
- **Genre Taxonomy**: Physical / Micro-Kinetic
- **Physics & Kinematics**:
  - Hexagonal spire lattice coordinates: $x = \text{col} \cdot d + (\text{row} \bmod 2) \cdot (d/2)$, $y = \text{row} \cdot d \frac{\sqrt{3}}{2}$ ($d = 105.0$).
  - Gaussian radial amplitude envelope: $\exp(-(r / 370.0)^2)$.
  - Harmonic traveling wave: $\sin(2\omega t - k r + m \theta)$ driving spire height ($H \in [80, 160]$) and base radius ($R \in [37, 55]$).
  - Depth-sorted back-to-front rendering order for accurate 3D conical occlusion.
- **Materiality & Lighting**:
  - Ground: Deep magnetic obsidian laboratory substrate (`#0a0c11`).
  - Fluid Surface: Jet-black petroleum fluid with multi-tier capillary meniscus depression rings (`#183048`).
  - Cones: 24-segment triangular mesh per spire with metallic Blinn-Phong specular calculation, reflecting rotating magnetic illumination.
  - Apex Beads: Electric cyan magnetic concentration nodes (`#38bdf8`) with soft halo auras.
  - Field Contours: Quadrupole and dipole isopotential flux contours and dynamic magnetic azimuth compass dial.
- **Anonymity**: 100% autonomous algorithmic generative art without human authorship marks, signatures, or name seals.

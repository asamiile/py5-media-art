# kinetic_ferrofluid_rosensweig_hexagonal_peaks_2d

**kinetic_ferrofluid_rosensweig_hexagonal_peaks_2d** is an algorithmic media art animation simulating the ferrohydrodynamics and non-linear surface peak bifurcation of the **Rosensweig normal-field instability** in a liquid mirror magnetic fluid pool, modeling the gyroscopic precession of a hexagonal array of conical spikes under a rotating magnetic field, coupled with 3D liquid chrome Blinn-Phong specular reflections and leaping superparamagnetic tracer sparks.

## Concept & Ferrohydrodynamics

When a horizontal layer of magnetic fluid (ferrofluid) is subjected to a vertical magnetic field $B$ exceeding the critical Rosensweig threshold $B_c = \sqrt{2 \rho g \mu_0 / (\sqrt{\rho g / \sigma})}$:

- **Hexagonal Rosensweig Peak Solitons**:
  The flat surface spontaneously destabilizes into a periodic hexagonal array of sharp conical spikes (Cowley & Rosensweig 1967). Lateral magnetic dipole repulsion balances surface tension and gravitational pooling, locking the peaks into a stable triangular/hexagonal lattice.
- **Precessing Rotating Magnetic Field**:
  Subjected to a rotating transverse magnetic perturbation $\mathbf{B}(t) = (B_\perp \cos(\omega t - \phi(r)), B_\perp \sin(\omega t - \phi(r)), B_0)$, each conical peak tilts, precesses, and undergoes continuous gyroscopic wobbling with a radial phase lag, radiating spiral magnetic capillary waves across the pool.
- **Liquid Mirror Blinn-Phong Specular Reflections**:
  Pure ferrofluid has high optical absorption and near-zero diffuse scattering, behaving as an ideal black liquid chrome mirror. Directional key (Electric Cyan) and rim (Molten Bronze/Amber) studio illuminations produce razor-sharp anisotropic specular highlights across the precessing conical slopes.
- **Leaping Superparamagnetic Tracer Sparks**:
  High-gradient magnetic fringing fields between neighboring spike tips accelerate luminous nanoscale tracer particles along parabolic flux arches, creating kinetic electric leaps and glowing trajectories.

## Visual Composition (60-30-10 Palette)

- **60% Liquid Chrome / Ferrofluid Obsidian Mirror**: Deep black obsidian liquid chrome (`#010206`, `#050814`) with Fresnel reflection sheens along the tilted spike skirts.
- **30% Metallic Silver & Electric Cyan / Cobalt Highlights**: Radiant Electric Cyan (`#00f2fe`, `#38bdf8`) and metallic silver-white catching the upper key light reflections.
- **10% Needle Spike Tips & Magnetic Sparks**: Blazing Molten Gold (`#f59e0b`, `#fbbf24`), Solar Amber, and pure Diamond White (`#ffffff`) marking peak singularities and leaping magnetic tracer sparks.

## Execution

```bash
uv run python sketch/kinetic_ferrofluid_rosensweig_hexagonal_peaks_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_ferrofluid_rosensweig_hexagonal_peaks_2d.mp4`)
- Preview snapshot: `kinetic_ferrofluid_rosensweig_hexagonal_peaks_2d_p1.png`

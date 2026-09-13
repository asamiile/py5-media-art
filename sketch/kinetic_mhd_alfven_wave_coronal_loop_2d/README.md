# kinetic_mhd_alfven_wave_coronal_loop_2d

**kinetic_mhd_alfven_wave_coronal_loop_2d** is an algorithmic media art animation simulating the non-linear magnetohydrodynamics (MHD) of **torsional Alfvén wave cascades**, **braided magnetic flux ropes**, and **Parker nanoflare heating** in solar coronal plasma loops.

## Concept & Solar Coronal Loop Magnetohydrodynamics

Coronal loops are majestic arches of incandescent magnetized plasma tracing closed dipolar magnetic flux tubes in the solar atmosphere. Anchored deep in the dense, convective solar photosphere, coronal loops solve the longstanding "Coronal Heating Problem" (why the solar corona reaches millions of Kelvin while the surface is only 5800 K) via non-equilibrium magnetic energy dissipation.

1. **Counter-Propagating Elsässer Alfvén Wave Cascades**:
   Photospheric convective granulations vigorously twist and shuffle magnetic footpoints, launching torsional shear Alfvén waves that propagate upwards along the flux ropes at Alfvén speed:
   $$v_A = \frac{B}{\sqrt{\mu_0 \rho}}$$
   Non-linear wave interactions between upward-traveling wave packets $z^+ = \vec{v} + \vec{b}$ and counter-propagating packets $z^- = \vec{v} - \vec{b}$ drive an MHD turbulent cascade, transferring Poynting flux from large driving scales down to resonant kinetic dissipation scales.

2. **Braided Magnetic Flux Strands & Parker Nanoflare Reconnection**:
   A single coronal loop consists of multiple braided magnetic sub-strands. Continuous footpoint twisting tangles adjacent field lines, generating intense sheet-like currents $\vec{J} = \nabla \times \vec{B}$. When the magnetic twist exceeds the Kruskal-Shafranov threshold, magnetic reconnection snaps the flux ropes, releasing magnetic energy in intermittent, incandescent micro-explosions known as **nanoflares**:
   $$Q_{\text{heat}} \sim \eta J^2$$

3. **Field-Aligned Plasma Transport & Chromospheric Spicules**:
   Thermal solar ions and relativistic reconnection electrons are magnetically confined to helical Larmor orbits around magnetic field vectors $\vec{B}$, accelerating upwards from chromospheric footpoints into the coronal apex and condensing as luminous coronal rain.

## Visual Composition (60-30-10 Palette)

- **60% Solar Corona Obsidian Void & Deep Chromospheric Indigo**: Deep space corona background (`#020108`) and chromospheric cooling gradient (`#0a0618`, `#140924`).
- **30% Braided Magnetic Flux Ropes Electric Amber, Solar Gold & Coronal Cyan**: Braided magnetic flux strands (`#f59e0b`, `#fbbf24`), wave modulation channels, and coronal sheath glow (`#06b6d4`, `#0284c7`).
- **10% Incandescent Nanoflare Reconnection Diamond-White & Extreme UV Violet**: Blinding white magnetic reconnection current sheets (`#ffffff`, `#fef08a`) and extreme ultraviolet (EUV) fluorescence halos (`#e879f9`, `#a855f7`).

## Execution

```bash
uv run python sketch/kinetic_mhd_alfven_wave_coronal_loop_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_mhd_alfven_wave_coronal_loop_2d.mp4`)
- Preview snapshot: `kinetic_mhd_alfven_wave_coronal_loop_2d_p1.png`

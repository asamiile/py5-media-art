# kinetic_andreev_reflection_bound_states_2d

2D quantum condensed matter physics simulation depicting Bogoliubov-de Gennes quasiparticle dynamics, Andreev retro-reflection at superconductor-normal-superconductor (SNS) interfaces, quantized Andreev bound state resonances, and macroscopic Cooper pair condensation.

## Concept & Physics

In a mesoscopic Superconductor-Normal-Superconductor (SNS) junction:
1. **Andreev Reflection**: An incident electron from the normal metal cavity with excitation energy below the superconducting gap ($E < \Delta$) cannot enter the superconductor as a single quasiparticle. Instead, it pairs with another electron of opposite spin and momentum, entering the macroscopic superconducting condensate ($\Psi = \Delta_0 e^{i\phi}$) as a Cooper pair ($2e$).
2. **Time-Reversal Retro-Reflection**: To conserve charge, energy, and momentum, a **hole** ($+e$) is retro-reflected along the exact incident trajectory of the incoming electron, reversing its velocity ($\mathbf{v}_h = -\mathbf{v}_e$).
3. **Andreev Bound States (ABS)**: Multiple Andreev reflections at both interfaces ($e \to h \to e \dots$) produce coherent phase interference and form discrete, quantized standing-wave resonances inside the cavity with energy $E(\Delta\phi) = \pm \Delta_0 \sqrt{1 - D \sin^2(\Delta\phi / 2)}$.
4. **Macroscopic Condensate Ripples**: In the superconducting leads, Cooper pair injection and oscillating Josephson phase differences $\Delta\phi(t)$ radiate 2D concentric phase wavefronts.
5. **Lagrangian Quasiparticles & Ribbon Trails**: 2,400 quasiparticles (Cyan electrons, Magenta holes, and Gold/Pearl Cooper pairs) trace glowing history ribbons illustrating time-reversed retro-reflection and bound-state orbits.

## Aesthetics & Color Palette

- **Superconducting Leads Bulk**: Deep Cryogenic Azure Cobalt & Radiant Cyan Ripples (`#0c2d6f` to `#00e1ff`)
- **Normal Cavity Resonances**: Deep Quantum Well Midnight Violet & Radiant Amethyst (`#1c0c30` to `#d414aa`)
- **Incident Electrons**: Luminous Electric Glacial Cyan (`#00e1ff`)
- **Retro-Reflected Holes**: Neon Laser Magenta / Radiant Cerise (`#ff19b9`)
- **Cooper Pairs & Specular Barrier Sheen**: Incandescent Liquid Pearl White & Solar Gold (`#ffffff` to `#ffe08c`)

## Specifications

- **Format**: Seamless looping animation (720 frames @ 60 FPS, 12 seconds)
- **Resolution**: 1920×1080 (HD preview) / 3840×2160 (4K master)
- **Engine**: py5 (Python Processing) + NumPy vectorized field tensor synthesis + Blinn-Phong dual-light specular normal mapping + vectorized batch trail rendering (`py5.lines()`, `py5.points()`)

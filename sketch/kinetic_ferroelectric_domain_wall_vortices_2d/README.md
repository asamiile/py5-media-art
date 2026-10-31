# kinetic_ferroelectric_domain_wall_vortices_2d

2D condensed matter and polar topology simulation depicting ferroelectric domain textures, 90° and 180° domain walls, flux-closure polarization vortices, and quasi-1D conductive domain wall electron transport.

## Concept & Physics

In nanoscale ferroelectric perovskite oxides (such as $\text{PbTiO}_3 / \text{SrTiO}_3$ superlattices and $\text{BiFeO}_3$), electrostatic boundary conditions and elastic strain relaxation drive the spontaneous formation of complex topological dipolar structures:
1. **Polarization Texture & Ginzburg-Landau Order**: Spontaneous electric polarization $\mathbf{P}(x, y)$ forms alternating orthogonal domains (tetragonal distortion variants $a_1/a_2$ and $c$-domains). Saturation occurs via non-linear double-well Landau-Devonshire energy potentials ($\tanh$ spatial locking).
2. **Topological Flux-Closure Vortices**: To minimize depolarizing electrostatic fields, opposing polarization sheets bend into continuous swirling vortices and antivortices characterized by integer winding numbers, channeling electric flux into closed toroidal loops.
3. **Domain Walls as Nano-Electronics**: The interfaces separating domains (both charge-neutral 90° walls and charged head-to-head / tail-to-tail 180° walls) exhibit localized structural symmetry breaking, severe band-gap narrowing, and carrier accumulation. These walls act as self-assembled, reconfigurable 1D conducting nanowires.
4. **Drift & Conduction Kinetics**: 1,600 mobile charge carriers (electrons and oxygen vacancies) stream along the incandescent conductive domain boundaries and circulate within topological vortex cores under applied bias and thermal fluctuations.

## Aesthetics & Color Palette

- **Opposing Polar Domains**: Saturated Ultramarine Blue (`#1a36e8`) and Vivid Carmine Crimson (`#e61a4c`)
- **Vortex Torus & Shearing Zones**: Luminous Cyan / Turquoise (`#26e6e6`) and Radiant Magenta
- **Conductive Domain Walls**: Blinding Incandescent Superconductive Gold/White Filament Glow (`#fffdf0` to `#ffe066`)
- **Conducting Charge Carriers**: High-luminescence spark points and trailing gold/cyan streamlines
- **Dielectric Substrate Ground**: Deep Obsidian Crystal Void (`#04060c`)

## Specifications

- **Format**: Seamless looping animation (720 frames @ 60 FPS, 12 seconds)
- **Resolution**: 1920×1080 (HD preview) / 3840×2160 (4K master)
- **Engine**: py5 (Python Processing) + NumPy vectorized Landau-Devonshire polarization field synthesis + spatial derivative domain-wall metric tensor + vectorized batch trail rendering (`py5.lines()`, `py5.points()`)

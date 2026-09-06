# kinetic_faraday_quasicrystal_resonances_2d

**kinetic_faraday_quasicrystal_resonances_2d** is an algorithmic media art animation simulating the parametric fluid dynamics and non-linear wave-mode triad resonances of **12-fold (dodecagonal) Faraday quasicrystals** in a two-frequency vertically driven liquid bath, coupled with 3D specular liquid-metal optics and bouncing pilot-wave surface micro-droplets.

## Concept & Non-Linear Hydrodynamics

When a liquid layer is subjected to two-frequency vertical vibration $g(t) = g_0 + \gamma_1 \cos(\omega_1 t) + \gamma_2 \cos(\omega_2 t + \chi)$, the standard square or hexagonal subharmonic Faraday standing waves bifurcate into aperiodic **dodecagonal (12-fold) Faraday quasicrystals**:

$$\zeta(\mathbf{r}, t) = \cos(\omega_1 t) \sum_{j=1}^{12} A_j \cos(\mathbf{k}_j \cdot \mathbf{r} + \phi_j) + \beta \cos(\omega_2 t + \chi) \sum_{j=1}^{12} B_j \cos(\mathbf{q}_j \cdot \mathbf{r} + \psi_j)$$

- **12-Fold Penrose Orientational Order**:
  Wavevectors $\mathbf{k}_j$ lie on a circle spaced by $\Delta \theta = 30^\circ$. Due to quadratic and cubic non-linear triad interactions between $k_1$ and $k_2 = 2 k_1 \cos(\pi/12)$, the standing wave pattern exhibits perfect 12-fold rotational symmetry without spatial periodicity, forming an aperiodic Penrose-like liquid surface tiling.
- **Parametric Resonance & Surface Curvature**:
  The subharmonic temporal beating produces continuous rhythmic pulsing, breathing, and phase inversions between wave peaks and deep obsidian troughs. Surface normal vectors $\mathbf{N} = (-\nabla \zeta, 1) / \sqrt{1 + |\nabla \zeta|^2}$ dictate directional Blinn-Phong specular reflections under chromatic key and rim lighting.
- **Bouncing Pilot-Wave Hydrodynamic Droplets**:
  Sub-millimeter liquid micro-droplets bounce synchronously on the vibrating surface, propelled by horizontal wave slope forces $\mathbf{F} \approx - m g \nabla \zeta$. The droplets navigate through the aperiodic potential landscape, tracing radiant orbits and hydrodynamic wakes.

## Visual Composition (60-30-10 Palette)

- **60% Deep Liquid Obsidian Mirror**: Abyssal midnight ocean base (`#02040c`, `#060b1e`) reflecting minimal ambient light in the deep wave troughs.
- **30% 12-Fold Quasicrystal Interference Ribs & Specular Caustics**: Iridescent Electric Cyan (`#00f2fe`) and Royal Amethyst / Magenta (`#d946ef`, `#8b5cf6`) tracing the liquid metallic slopes under dual key and rim studio illumination.
- **10% Quasicrystal Crest Singularities & Bouncing Droplets**: Blazing Solar Gold (`#ffd600`, `#ffea75`) and pure Diamond White (`#ffffff`) marking maximum curvature crest spikes and bouncing pilot-wave micro-droplets.

## Execution

```bash
uv run python sketch/kinetic_faraday_quasicrystal_resonances_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_faraday_quasicrystal_resonances_2d.mp4`)
- Preview snapshot: `kinetic_faraday_quasicrystal_resonances_2d_p1.png`

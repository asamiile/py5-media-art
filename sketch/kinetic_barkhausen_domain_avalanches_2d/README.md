# kinetic_barkhausen_domain_avalanches_2d

**kinetic_barkhausen_domain_avalanches_2d** is an algorithmic media art animation simulating the non-equilibrium physics of **Barkhausen noise**, magnetic domain wall pinning, and self-organized critical avalanches in a disordered ferromagnetic thin film.

## Concept & Physics

In ferromagnets subjected to an alternating magnetic field $H_{\text{ext}}(t)$, magnetic domain walls do not advance smoothly; instead, they become pinned against microscopic material defects, non-magnetic inclusions, and crystallographic grain boundaries. As the external field intensifies, local pinning thresholds are exceeded, triggering sudden, localized unpinning bursts known as **Barkhausen avalanches**:

$$\frac{\partial m}{\partial t} = \kappa \nabla^2 m + (m - m^3) + H_{\text{ext}}(t) + \xi_{\text{pin}}(\mathbf{x}) - \eta \langle m \rangle$$

- **Allen-Cahn Order Parameter ($m \in [-1, 1]$)**: Governs bistable up/down magnetization domains with surface tension across domain walls.
- **Quenched Disorder Landscape ($\xi_{\text{pin}}$)**: Multi-scale defect clusters with power-law distributed pinning strengths.
- **Cyclic Zeeman Field ($H_{\text{ext}}(t)$)**: Alternating driving field causing periodic hysteresis cycles, wall creep, and explosive unpinning cascades.
- **Acoustic Radiation ($\mathcal{A}(\mathbf{x}, t) = |\partial m / \partial t|$)**: Radiating shock waves and luminous acoustic emission sparks ejected tangentially along rapidly advancing domain fronts.
- **Polycrystalline Anisotropy**: Underlying Voronoi crystallographic grains with distinct magnetic easy axes and grain boundary facets.

## Visual Composition (60-30-10 Palette)

- **60% Polycrystalline Obsidian Matrix**: Deep indigo and obsidian slate domains (`#050811`, `#121e3d`) layered with subtle anisotropic micro-striations and grain boundaries.
- **30% Electric Turquoise Domain Walls**: Glowing bioluminescent-like cyan and electric turquoise boundary lines (`#00e5c0`, `#14b8a6`, `#38bdf8`) tracing domain contours and radiating diffusive shock wave ripples.
- **10% Incandescent Avalanche Bursts & Sparks**: Blazing solar amber (`#f59e0b`), molten gold (`#fbbf24`), and diamond-white cores (`#ffffff`) marking violent unpinning events accompanied by high-velocity acoustic emission sparks.

## Execution

```bash
uv run python sketch/kinetic_barkhausen_domain_avalanches_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_barkhausen_domain_avalanches_2d.mp4`)
- Preview snapshot: `kinetic_barkhausen_domain_avalanches_2d_p1.png`

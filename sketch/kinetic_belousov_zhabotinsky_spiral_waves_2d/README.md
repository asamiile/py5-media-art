# kinetic_belousov_zhabotinsky_spiral_waves_2d

**kinetic_belousov_zhabotinsky_spiral_waves_2d** is an algorithmic media art animation simulating the non-linear chemical reaction-diffusion dynamics of the **Belousov-Zhabotinsky (BZ) reaction** and the **Oregonator / Tyson-Fife model**, capturing the self-organization of multi-rotor Archimedean spiral waves, chiral rotor meanderings, topological phase singularities, and mutual wave annihilation along collision shock fronts.

## Concept & Chemical Reaction-Diffusion Physics

In an unstirred thin layer containing malonic acid, bromate, and a ferroin/ferriin transition-metal redox catalyst ($Fe^{2+} / Fe^{3+}$), autocatalytic oxidation of bromous acid ($HBrO_2$) triggers rotating spiral waves in the complex chemical state:

$$\frac{\partial \mathbf{c}}{\partial t} = \mathbf{D} \nabla^2 \mathbf{c} + \mathbf{F}(\mathbf{c})$$

- **Archimedean Chemical Spiral Rotors**:
  Phase singularities at rotor tips serve as catalytic organizing centers. The spiral wavefront phase follows $\phi_j = s_j \theta_j - k r_j + \omega_j t$, where $s_j = \pm 1$ represents the topological topological winding chirality (dextrorotatory vs levorotatory).
- **Rotor Meandering & Core Nutation**:
  The chemical wave tips execute hypocycloidal meander orbits across the medium, modulating local curvature and spiral pitch.
- **Wave Collision Annihilation**:
  Because the medium directly behind an advancing oxidation wavefront enters a refractory period (high inhibitor concentration), colliding chemical waves do not pass through each other; instead, they annihilate upon contact, creating dynamic shock boundaries and polygonal reaction domains.
- **Catalytic Indicator Tracer Sparks**:
  Microscopic colloidal precipitate particles and fluorescent redox sparks advect along the normal gradients of the chemical wavefronts, illuminating the active reaction zones with incandescent luminescence.

## Visual Composition (60-30-10 Palette)

- **60% Reduced Catalyst Matrix Base**: Deep Ferroin Obsidian and Abyssal Maroon (`#030107`, `#080412`), representing the reduced state of the chemical reagent substrate.
- **30% Oxidized Catalytic Fronts & Refractory Wakes**: Luminescent Ferriin Electric Cyan (`#00f8e1`) and Jade Emerald (`#00e6a8`), contrasted against a Neon Violet and Royal Amethyst (`#a824e8`, `#381078`) excitation halo and refractory wave wake.
- **10% Rotor Singularity Cores & Annihilation Peaks**: Solar Amber (`#ffd060`) and pure Incandescent White (`#ffffff`) marking topological rotor tips, high-density chemical wavefront peaks, and micro-spark trails.

## Execution

```bash
uv run python sketch/kinetic_belousov_zhabotinsky_spiral_waves_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_belousov_zhabotinsky_spiral_waves_2d.mp4`)
- Preview snapshot: `kinetic_belousov_zhabotinsky_spiral_waves_2d_p1.png`

# kinetic_rayleigh_taylor_kelvin_helmholtz_mushrooms_2d

2D hydrodynamic simulation depicting multi-mode Rayleigh-Taylor interfacial instability with Atwood number density stratification ($A_t \approx 0.6$), baroclinic vorticity generation ($\frac{1}{\rho^2} \nabla \rho \times \nabla p$), and secondary Kelvin-Helmholtz mushroom vortex rollups.

## Concept & Physics

When a heavier fluid ($\rho_2$) rests upon a lighter fluid ($\rho_1$) in an effective gravitational acceleration field $\mathbf{g}$, any interfacial perturbation $\eta(x, 0)$ is unstable to the Rayleigh-Taylor instability with exponential growth rate $\gamma = \sqrt{A_t g k}$.

In the non-linear stage:
1. **Spikes and Bubbles**: Dense fluid descends as narrow, penetrating spikes, while light fluid rises as rounded bubbles.
2. **Kelvin-Helmholtz Shear Rollups**: The velocity shear along the spike-bubble interface triggers secondary Kelvin-Helmholtz rollups, rolling the interface into nested pairs of spiraling mushroom caps.
3. **Baroclinic Vorticity**: The misaligned density and pressure gradients ($\nabla \rho \times \nabla p \neq 0$) generate intense vorticity sheets along the mushroom flanks.
4. **Specular Meniscus Highlights**: Dual-light Blinn-Phong specular shading reveals the undulating liquid meniscus like polished molten amber and deep sapphire glass.
5. **Lagrangian Tracers**: 4,500 fluid tracer particles reveal the swirling circulation and vortex core entrainment.

## Aesthetics & Color Palette

- **Dense Upper Fluid**: Deep Obsidian Indigo & Sapphire Abyss (`#091634` to `#102450`)
- **Light Lower Fluid**: Molten Solar Amber & Radiant Gold (`#f59116` to `#ffd030`)
- **Shear Mixing Layer & Mushroom Spirals**: Phosphorescent Emerald Teal (`#00ffb4`) & Coral Violet (`#a020f0`)
- **Specular Liquid Sheen**: Incandescent Liquid Pearl White (`#ffffff`)

## Specifications

- **Format**: Seamless looping animation (900 frames @ 60 FPS, 15 seconds)
- **Resolution**: 1920×1080 (HD preview) / 3840×2160 (4K master)
- **Engine**: py5 (Python Processing) + NumPy vectorized fluid density field + Blinn-Phong dual-light specular normal mapping

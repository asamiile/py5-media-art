# kinetic_fitzhugh_nagumo_excitable_waves_2d

A 4K kinetic visualization of excitable media waves using the FitzHugh-Nagumo reaction-diffusion model, simulating electrical wave propagation through neural fabrics.

![Preview](kinetic_fitzhugh_nagumo_excitable_waves_2d_p1.png)

## Concept

The FitzHugh-Nagumo (FHN) model is a simplified 2-variable reaction-diffusion model of nerve action potentials:
$$\frac{\partial u}{\partial t} = D_u \nabla^2 u + u - u^3 - v$$
$$\frac{\partial v}{\partial t} = D_v \nabla^2 v + \epsilon (u - a_0 v - a_1)$$
where $u$ represents the activator (membrane potential) and $v$ represents the inhibitor (refractory state variable). Propagating wave fronts curl into spirals upon colliding or encountering spatial gradients, producing complex self-organizing pattern dynamics.

## Techniques

- **FitzHugh-Nagumo PDE Integration**: Solves the coupled excitable media equations using explicit Euler time-stepping.
- **Vectorized Finite-Difference Laplacian**: Vectorized periodic boundary Laplacian calculations via fast NumPy array rolls.
- **Bilinear Upscaling**: Bilinearly stretches a $1280 \times 720$ simulation grid to full $3840 \times 2160$ 4K resolution inside `py5.np_pixels`.
- **Hybrid HSB-RGB Color Mapping**: Maps activator concentration to glowing cyan fronts, inhibitor concentration to ultraviolet tails, and highlights high-gradient wave collisions in golden phosphor amber.

## Palette

- **Background**: Obsidian Abyss (near-black, 12, 10, 16)
- **Dominant**: Bioluminescent Cyan (wave front, 0, 240, 220)
- **Secondary**: Deep Ultraviolet (refractory zone, 100, 30, 220)
- **Accent**: Phosphor Amber (excitation cores, 250, 160, 20)

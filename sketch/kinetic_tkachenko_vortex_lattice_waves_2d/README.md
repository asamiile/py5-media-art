# kinetic_tkachenko_vortex_lattice_waves_2d

**kinetic_tkachenko_vortex_lattice_waves_2d** is an algorithmic media art animation simulating the quantum hydrodynamic elasticity of a rotating Bose-Einstein Condensate / superfluid helium, focusing on the propagation of **Tkachenko transverse shear waves** across a triangular Abrikosov quantized vortex lattice.

## Concept & Quantum Physics

In a rapidly rotating superfluid, macroscopic angular momentum enters in the form of a periodic triangular array of quantized vortices known as an **Abrikosov lattice**. Unlike classical vortex sheets, this crystalline lattice of topological singularities exhibits a non-vanishing macroscopic shear modulus $C_2$:

$$C_2 = \frac{\hbar \Omega \rho_s}{8 m}$$

- **Tkachenko Transverse Shear Modes**:
  Discovered by I.F. Tkachenko (1966), transverse elastic shear waves propagate through the vortex lattice with linear acoustic dispersion $\omega(k) \propto k$:
  $$\delta \mathbf{r}_j(t) = \sum_m A_m \hat{\mathbf{e}}_{\perp, m} \sin(\mathbf{k}_m \cdot \mathbf{r}_j - \omega_m t)$$
  Vortices oscillate transversely to their wavevector, creating dynamic breathing patterns, shear strains, and local lattice compressions.
- **Topological Voronoi Lattice Cell Elasticity**:
  The Voronoi partition of the vortex lattice ($d_{\text{second}} - d_{\text{nearest}}$) generates razor-sharp hexagonal Wigner-Seitz cells that flex, stretch, and dynamically deform under the passing Tkachenko wave packets.
- **Macroscopic Order Parameter $\Psi(\mathbf{r})$ & Phase Singularities**:
  The complex superfluid wavefunction wraps phase by $2\pi$ around each quantized vortex core:
  $$\Psi(\mathbf{r}) = \prod_j \tanh\left(\frac{|\mathbf{r} - \mathbf{r}_j|}{\xi}\right) e^{i \theta_j(\mathbf{r})}$$
  Interference between multiple winding phases creates intricate topological equiphase streamlines connecting neighboring vortex cores.
- **Trapped Exciton / Quantum Impurity Particles**:
  Fluorescent microscopic quantum impurities and excitons are trapped in the pressure minima of the circulating vortex cores ($\mathbf{v}_s = \frac{\hbar}{m r} \hat{\boldsymbol{\theta}}$), tracing glowing orbital ribbons as the vortex cores dance in Tkachenko orbits.

## Visual Composition (60-30-10 Palette)

- **60% Deep Cryogenic Superfluid Matrix**: Deep quantum vacuum indigo and midnight sapphire (`#02040d`, `#050b1a`, `#0a1c38`) carrying ambient condensate density and radiating acoustic phonon ripples.
- **30% Voronoi Elastic Shear Boundaries & Phase Streamlines**: Luminous electric cyan (`#00e5ff`) and neon emerald (`#00ffa3`) tracing flexing hexagonal cell walls, intertwined with vibrant neon magenta and electric violet (`#ff007f`, `#d100ff`) topological phase sheets.
- **10% Quantized Vortex Cores & Trapped Impurities**: Blazing solar gold (`#ffea75`, `#ffb703`) and diamond-white (`#ffffff`) marking vortex singularities and trapped orbital quantum impurities.

## Execution

```bash
uv run python sketch/kinetic_tkachenko_vortex_lattice_waves_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_tkachenko_vortex_lattice_waves_2d.mp4`)
- Preview snapshot: `kinetic_tkachenko_vortex_lattice_waves_2d_p1.png`

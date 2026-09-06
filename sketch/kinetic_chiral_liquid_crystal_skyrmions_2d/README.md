# kinetic_chiral_liquid_crystal_skyrmions_2d

**kinetic_chiral_liquid_crystal_skyrmions_2d** is an algorithmic media art animation simulating the non-linear topological physics and optical birefringence of **chiral nematic liquid crystal baby skyrmions** observed under a **Polarizing Optical Microscope (POM)** with crossed polarizers.

## Concept & Physics

In chiral liquid crystal thin films, competitive Frank-Oseen elastic deformation and chiral dopant twisting stabilize localized particle-like topological solitons known as **chiral baby skyrmions**:

$$\mathbf{n}(\mathbf{r}) = \left( \sin\theta(r) \cos\phi(\alpha), \; \sin\theta(r) \sin\phi(\alpha), \; \cos\theta(r) \right)$$

- **Topological Invariant ($Q = \pm 1$)**: The molecular director $\mathbf{n}$ wraps the unit sphere $S^2$ with integer topological charge:
  $$Q = \frac{1}{4\pi} \iint \mathbf{n} \cdot \left( \frac{\partial \mathbf{n}}{\partial x} \times \frac{\partial \mathbf{n}}{\partial y} \right) dx dy$$
- **Polarizing Optical Microscopy (POM) & Maltese Crosses**:
  Under crossed linear polarizers, transmitted intensity is governed by the optical retardation $\delta(\mathbf{r}) = (1 - n_z^2) \frac{2\pi \Delta n d}{\lambda}$:
  $$\mathcal{I}(\mathbf{r}) \propto \sin^2(2\phi(\mathbf{r})) \sin^2\left(\frac{\delta(\mathbf{r})}{2}\right)$$
  This produces iconic four-arm **Maltese cross isogyres** (regions where $\mathbf{n}$ aligns with the polarizer or analyzer) and concentric multi-order **Michel-Lévy birefringent interference rings**.
- **Chiral Skyrmion Hall Drift**:
  Driven by an alternating in-plane AC electric field, skyrmions ($Q=+1$) and antiskyrmions ($Q=-1$) experience opposite gyro-vector deflections ($\mathbf{G} \times \mathbf{v}$), tracing intertwining hypocycloid paths across the polarized optical field.
- **Trapped Fluorescent Colloidal Nanoparticles**:
  Dielectric colloidal micro-particles minimize elastic Frank energy by trapping themselves along the Saturn defect rings of the skyrmions, forming luminous orbital tracer swarms.

## Visual Composition (60-30-10 Palette)

- **60% Homeotropic Dark Obsidian Extinction**: Deep midnight space (`#020309`, `#080d1a`) where vertical director orientation produces complete optical extinction under crossed polarizers.
- **30% Iridescent Birefringent Interference Fringes**: Vivid peacock cyan (`#06b6d4`), electric emerald (`#10b981`), and royal amethyst/magenta (`#a855f7`, `#ec4899`) tracing the tilted director zones and Maltese isogyres.
- **10% Topological Defect Cores & Trapped Colloids**: Blazing solar amber (`#f59e0b`), molten gold (`#fbbf24`), and diamond-white (`#ffffff`) marking homeotropic core inversion rings and orbiting fluorescent tracer particles.

## Execution

```bash
uv run python sketch/kinetic_chiral_liquid_crystal_skyrmions_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_chiral_liquid_crystal_skyrmions_2d.mp4`)
- Preview snapshot: `kinetic_chiral_liquid_crystal_skyrmions_2d_p1.png`

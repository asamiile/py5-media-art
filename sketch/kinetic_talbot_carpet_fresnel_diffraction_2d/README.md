# kinetic_talbot_carpet_fresnel_diffraction_2d

**kinetic_talbot_carpet_fresnel_diffraction_2d** is an algorithmic media art animation simulating the near-field wave optics of the **Talbot Effect**, **Fresnel diffraction carpets**, **integer and fractional self-imaging revivals**, and **Bohmian optical flow trajectories**.

## Concept & Wave Mechanics

Discovered by Henry Fox Talbot in 1836 and analyzed within quantum mechanics by Berry and Klein, the Talbot effect occurs when a monochromatic wave illuminates a periodic transmission diffraction grating of pitch $d$.

1. **Paraxial Fresnel Propagator & Quadratic Phase Dispersion**:
   The spatial Fourier harmonics of the grating acquire a quadratic longitudinal phase shift during paraxial wave propagation along distance $z$:
   $$\psi(x, z) = \sum_{n=-N}^N c_n \exp\left( i \frac{2\pi n x}{d} - i 2\pi \frac{n^2}{z_T} z \right)$$
   where the characteristic Talbot length scale is:
   $$z_T = \frac{2 d^2}{\lambda}$$

2. **Integer & Fractional Self-Imaging Revivals**:
   - At integer multiples $z = m \cdot z_T$, all quadratic harmonic phases satisfy $2\pi m n^2 \equiv 0 \pmod{2\pi}$, reconstructing an exact replica of the original aperture grating (integer Talbot revival).
   - At half-Talbot distances $z = (m + 1/2) z_T$, the phase shift is $\pi n^2 \equiv \pi n \pmod{2\pi}$, reconstructing the grating with a spatial half-period transverse shift $x \to x + d/2$.
   - At rational fractions $z = (p/q) z_T$, constructive and destructive interference weave the legendary **Talbot Carpet**—a nested, self-similar fractal diamond tapestry with sub-harmonic periodicities $d/q$.

3. **Poynting Energy Streamlines & Topological Phase Singularities**:
   Energy flows along the Poynting momentum vector field:
   $$\vec{S}(x, z) = \frac{1}{|\psi|^2 + \epsilon} \operatorname{Im}\left( \psi^* \nabla \psi \right)$$
   At the zero-intensity nodal points, optical phase singularities (optical vortices) emerge with quantized topological circulation $\oint \nabla \phi \cdot d\vec{r} = \pm 2\pi$.

4. **3D Blinn-Phong Specular Relief & Bohmian Photon Kinematics**:
   The coherent optical intensity and phase landscape is shaded as a sculpted 3D optical crystal with dual light sources, while Lagrangian Bohmian photon packets stream along Poynting vector flux tubes through the caustic Talbot focal knots.

## Visual Composition (60-30-10 Palette)

- **60% Quantum Vacuum Obsidian Void & Deep Indigo Shadow**: Abyssal quantum background (`#020207`) and deep subterranean indigo shadows (`#070a18`, `#0e1228`).
- **30% Coherent Laser Azure & Electric Glacial Cyan Interference Fringes**: Fractal Talbot sub-harmonic diamond lattices and coherent wave ribbons (`#0284c7`, `#06b6d4`, `#38bdf8`, `#7dd3fc`).
- **10% Incandescent Talbot Focal Knots Diamond-White & Solar Gold Caustics**: Blinding constructive revival focal knots (`#ffffff`, `#fef08a`, `#fbbf24`), with electric violet vortex stars (`#c084fc`) and streaming Bohmian photon filaments.

## Execution

```bash
uv run python sketch/kinetic_talbot_carpet_fresnel_diffraction_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_talbot_carpet_fresnel_diffraction_2d.mp4`)
- Preview snapshot: `kinetic_talbot_carpet_fresnel_diffraction_2d_p1.png`

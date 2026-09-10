# kinetic_electrohydrodynamic_taylor_cone_2d

**kinetic_electrohydrodynamic_taylor_cone_2d** is an algorithmic media art animation simulating the non-linear physics of **electrohydrodynamics (EHD)** and the **Taylor cone singularity**, modeling Maxwell stress deformation of a conducting liquid meniscus, the formation of the universal $49.3^\circ$ conical tip, whipping/bending jet instabilities, and Coulomb-repulsed electrospray aerosol ionization.

## Concept & Electrohydrodynamic Mechanics

When an electric potential is applied between a conducting liquid meniscus and an opposing ground electrode, induced surface charge creates an outward Maxwell electrostatic stress:

$$T_M = \frac{1}{2} \epsilon_0 |\mathbf{E}|^2$$

At the critical Rayleigh limit, Maxwell stress overcomes surface tension $\gamma$, causing the rounded meniscus to abruptly deform into a conical cusp with a universal half-angle:

$$\theta_c = \arccos\left(\sqrt{1/3}\right) \approx 49.3^\circ$$

- **Singular Electric Field Concentration**:
  Near the conical tip, Laplace's equation $\nabla^2 \Phi = 0$ exhibits fractional-order spherical harmonics $P_{1/2}(\cos \theta)$, producing an electric field that scales inversely with the square root of tip distance ($|\mathbf{E}| \propto r^{-1/2}$), generating intense field-emission and local ionization.
- **Whipping Micro-Jet Instability**:
  From the Taylor cone apex, a supersonic liquid micro-jet is pulled upward. Due to charge buildup and aerodynamic drag, the jet undergoes a non-axisymmetric lateral whipping (kink) instability, forming dynamic serpentine helical loops.
- **Coulombic Electrospray Aerosol**:
  The whipping jet breaks up into monodisperse charged micro-droplets that fan out into a conical plume under mutual Coulombic electrostatic repulsion.
- **3D Specular Liquid Shading**:
  Dual Blinn-Phong specular highlights trace the deformed liquid surface, highlighting the tension and fluidity of the charged meniscus.

## Visual Composition (60-30-10 Palette)

- **60% High-Voltage Vacuum Obsidian & Royal Amethyst**: Deep vacuum space (`#030208`) and conducting fluid bulk (`#1e0836`, `#3b0764`), creating an abyss of electrical tension.
- **30% Ionizing Neon Violet & Ozone Cyan**: Radiant equipotential field lines (`#8b5cf6`), meniscus crest glints, and ozone-tinted electric streamlines (`#06b6d4`, `#38bdf8`).
- **10% Incandescent Solar White-Gold**: Taylor cone singular apex (`#fffbeb`), whipping jet core (`#fef08a`), and energetic electrospray ion sparks (`#ffffff`).

## Execution

```bash
uv run python sketch/kinetic_electrohydrodynamic_taylor_cone_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_electrohydrodynamic_taylor_cone_2d.mp4`)
- Preview snapshot: `kinetic_electrohydrodynamic_taylor_cone_2d_p1.png`

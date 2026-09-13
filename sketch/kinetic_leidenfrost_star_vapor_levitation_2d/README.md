# kinetic_leidenfrost_star_vapor_levitation_2d

**kinetic_leidenfrost_star_vapor_levitation_2d** is an algorithmic media art animation simulating the non-equilibrium hydrodynamics and thermo-capillary physics of an **oscillating Leidenfrost star droplet** levitating frictionless upon its self-generated boiling vapor cushion.

## Concept & Leidenfrost Thermo-Capillary Dynamics

When a liquid droplet is placed on a superheated solid surface well above its boiling point ($T_{\text{substrate}} \gg T_{\text{Leidenfrost}}$), the bottom liquid interface flash-boils, creating a continuous sub-micron vapor cushion. The vapor film thermally insulates the droplet from the substrate, eliminates solid-liquid shear friction, and supports the drop against gravity.

1. **Sub-Harmonic Polygonal Star Oscillations (Rayleigh-Lamb Capillary Modes)**:
   Free from boundary friction, the droplet perimeter spontaneously undergoes non-linear standing capillary wave oscillations transitioning through $m=3$ (triangular), $m=4$ (square), $m=5$ (pentagonal), $m=6$ (hexagonal), and $m=7$ (heptagonal) star modes:
   $$R(\theta, t) = R_0 \left[ 1 + \sum_{m=3}^{7} a_m(t) \cos(m(\theta - \Omega_m t) + \phi_m) \cos(\omega_m t) \right]$$
   where the eigenfrequencies follow the Rayleigh-Lamb capillary dispersion relation:
   $$\omega_m^2 = \frac{\gamma}{\rho R_0^3} m(m-1)(m+2)$$
   Non-linear hydrodynamic pressure steepening sharpens the expanding star lobes into prominent outward cusps.

2. **Vapor Layer Levitation & Thin-Film Optical Interference (Newton's Rings / Fabry-Pérot Fringes)**:
   Underneath the levitating drop, the variable sub-micron vapor layer thickness $h(r, \theta, t) \sim 10-50\,\mu\text{m}$ acts as an optical etalon, producing vibrant iridescent interference fringes (Newton's rings) that pulsate radially along the boiling meniscus:
   $$\Delta \Phi = \frac{4\pi}{\lambda} h(r, \theta, t)$$

3. **Internal Marangoni Toroidal Convection Vortices**:
   The steep thermal gradient between the superheated bottom vapor layer and the cooler evaporating top surface drives strong thermo-capillary surface-tension shear stresses:
   $$\tau = \nabla_s \gamma = \frac{d\gamma}{dT} \nabla_s T$$
   This induces counter-rotating toroidal Marangoni convection rolls within the liquid core, driving swirling tracer streamlines inside the droplet.

4. **Rayleigh-Plateau Capillary Tip Pinch-Off & Vapor Jet Wisps**:
   At peak lobed deformation, the high curvature tips exceed the capillary stability threshold, ejecting micro-satellite droplets and shimmering vapor wisps tangential to the oscillations into the surrounding ambient void.

5. **3D Surface Normal Gradient & Specular Liquid Chrome Shading**:
   The 3D height profile $H(r, \theta)$ is evaluated with analytical normal vectors $\vec{n} = (-\nabla H, 1) / \|\dots\|$ illuminated by dual moving point lights, yielding dynamic liquid mirror reflections across the undulating star lobes.

## Visual Composition (60-30-10 Palette)

- **60% Substrate Obsidian Void & Thermal Infrared Charcoal**: Superheated substrate vacuum background (`#030206`) and deep thermal radiating infrared charcoal (`#0c0716`, `#180f2d`).
- **30% Oscillating Liquid Core Cobalt, Glacial Azure & Marangoni Indigo**: Vibrating liquid droplet body (`#1e3a8a`), glacial surface chrome highlights (`#0284c7`, `#38bdf8`), and Marangoni convection streamlines.
- **10% Incandescent Vapor Cushion White-Gold & Thin-Film Iridescent Violet**: Incandescent meniscus rim and satellite pearls (`#fffbeb`, `#fef08a`), with thin-film optical interference fringes (`#e879f9`, `#06b6d4`).

## Execution

```bash
uv run python sketch/kinetic_leidenfrost_star_vapor_levitation_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_leidenfrost_star_vapor_levitation_2d.mp4`)
- Preview snapshot: `kinetic_leidenfrost_star_vapor_levitation_2d_p1.png`

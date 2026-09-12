# kinetic_polygonal_hydraulic_jump_2d

**kinetic_polygonal_hydraulic_jump_2d** is an algorithmic media art animation simulating the non-linear fluid mechanics of a **circular and polygonal hydraulic jump**, capturing supercritical thin-film radial expansion, Rayleigh-Plateau polygonal shockfront bifurcation, standing corner recirculation vortices, and Lagrangian micro-droplet kinematics.

## Concept & Hydrodynamic Jump Mechanics

When a vertical liquid jet impinges on a flat horizontal plane, fluid spreads radially thin at supercritical velocities where the Froude number exceeds unity ($Fr = u / \sqrt{g h} > 1$). At a critical radius $R_j$, momentum conservation forces an abrupt shock-like transition to subcritical flow ($Fr < 1$), accompanied by an abrupt increase in fluid layer depth:

$$\Delta h = \frac{h_1}{2} \left( \sqrt{1 + 8 Fr_1^2} - 1 \right)$$

- **Polygonal Star Instabilities**:
  Under azimuthal surface tension, adverse pressure gradients, and viscous boundary layer separation, the circular jump boundary breaks symmetry into rotating, pulsating polygonal star shapes (triangles, squares, pentagons, hexagons):
  $$R_j(\theta, t) = R_0 \cdot \left[1 + \sum_{m} A_m(t) \cos(m (\theta - \Omega_m t) + \phi_m)\right]$$
- **Corner Recirculation Vortices**:
  At each polygonal vertex where curvature is maximal, flow separation generates standing corner roller eddies that trap and circulate micro-droplets in dynamic golden whirlpools.
- **Capillary Wave Trains**:
  In the subcritical outer pool, surface tension excites concentric capillary ripple trains radiating outward before gently damping toward quiescent margins.
- **3D Specular Liquid Shading**:
  Dual-source Blinn-Phong specular lighting (an electric cyan key light and an amber rim light) illuminates surface gradients $\nabla h$, rendering the shockfront with the optical refraction and luminous sheen of flowing glass.

## Visual Composition (60-30-10 Palette)

- **60% Abyssal Hydrodynamic Obsidian & Cobalt**: Deep marine base (`#02060d`) and vitreous liquid cobalt (`#0a1f44`), grounding the dark fluid bath.
- **30% Bioluminescent Liquid Cyan & Aquamarine**: Fluorescent cyan (`#00f0ff`) and mint jade (`#0ae8b0`) defining the sharp shockfront ridge, thin-film streamlines, and capillary ripples.
- **10% Incandescent Solar Gold & Foam White**: Solar gold (`#ffe680`) and pure incandescent white (`#ffffff`) marking corner recirculation vortices, specular glints, and energetic droplet tracer sparks.

## Execution

```bash
uv run python sketch/kinetic_polygonal_hydraulic_jump_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_polygonal_hydraulic_jump_2d.mp4`)
- Preview snapshot: `kinetic_polygonal_hydraulic_jump_2d_p1.png`

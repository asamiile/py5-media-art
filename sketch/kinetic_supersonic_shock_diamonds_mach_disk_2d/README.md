# kinetic_supersonic_shock_diamonds_mach_disk_2d

**kinetic_supersonic_shock_diamonds_mach_disk_2d** is an algorithmic media art animation simulating compressible gas dynamics and aeroacoustic wave mechanics in an underexpanded supersonic rocket plume. The piece captures **Prandtl-Meyer expansion fans**, **oblique shock diamond reflections**, **normal Mach disk stems**, **acoustic screech resonance oscillations**, **Schlieren refractivity optics**, and **supersonic Lagrangian plasma spark kinematics**.

## Concept & Compressible Fluid Dynamics

When supersonic gas exhausts from a de Laval nozzle into an ambient environment where the exit pressure exceeds ambient pressure ($P_{exit} > P_{amb}$), the flow is **underexpanded**. To equilibrate pressure with the surrounding atmosphere, the supersonic stream establishes a self-organizing periodic chain of stationary shock cells known as **shock diamonds** or **Mach diamonds**:

1. **Prandtl-Meyer Expansion Fans**:
   At the nozzle lip, the flow turns outward through a centered expansion fan. As the gas expands, its static pressure and density drop precipitously while Mach number increases ($M > 2.5$).
2. **Oblique Shock Reflection**:
   The expansion waves propagate across the jet and impinge on the constant-pressure jet boundary, reflecting back into the core as compression waves that coalesce into conical **incident oblique shocks**.
3. **Mach Disk Formation & Triple Points**:
   When incident shocks converge along the jet centerline, regular oblique reflection becomes geometrically impossible. The shock structure bifurcates into a normal shock barrier—the **Mach disk** (or Mach stem). At the triple point where the incident shock, reflected shock, and Mach disk intersect, **slip lines** (shear contact discontinuities) shear downstream into the core.
4. **Thermodynamic Incandescence**:
   Across the normal Mach disk, the flow decelerates from supersonic to subsonic, causing a sudden spike in static temperature and density ($T_2/T_1 \gg 1$). This stagnation heating produces brilliant chemiluminescent combustion and ionized plasma emission.
5. **Acoustic Screech Feedback & Kelvin-Helmholtz Instability**:
   Large-scale coherent Kelvin-Helmholtz vortices convect along the outer shear layer and strike the fourth or fifth shock diamond cell, radiating acoustic feedback waves upstream to the nozzle lip. This closed feedback loop drives high-intensity **jet screech**—an aeroacoustic breathing mode that modulates the diamond spacing and sheds rhythmic vortex rings.

## Visual Composition (60-30-10 Palette)

- **60% Abyssal Void & Supersonic Expansion Cobalt/Indigo**: Dark cosmic vacuum (`#020409`) and supersonic expansion shadowgraph contours (`#0b192c`, `#152238`, `#1e293b`).
- **30% Ionized Shock Cyan & Electric Teal**: Oblique shock diamond knife-edges, slip lines, and Kelvin-Helmholtz vortex shear curls (`#00f0ff`, `#38bdf8`, `#06b6d4`).
- **30% Incandescent Mach Disk White-Gold & Core Violet**: Normal Mach disk stems, subsonic combustion hotspots, and high-velocity plasma sparks (`#ffffff`, `#fef08a`, `#f59e0b`, `#c084fc`).

## Execution

```bash
uv run python sketch/kinetic_supersonic_shock_diamonds_mach_disk_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_supersonic_shock_diamonds_mach_disk_2d.mp4`)
- Preview snapshot: `kinetic_supersonic_shock_diamonds_mach_disk_2d_p1.png`

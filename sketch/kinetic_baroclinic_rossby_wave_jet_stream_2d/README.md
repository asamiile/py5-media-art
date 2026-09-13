# kinetic_baroclinic_rossby_wave_jet_stream_2d

**kinetic_baroclinic_rossby_wave_jet_stream_2d** is an algorithmic media art animation simulating the geophysical fluid dynamics of **baroclinic instability**, planetary **Rossby wave jet stream meanders**, and cut-off **cyclonic cold pool eddies**.

## Concept & Geophysical Fluid Mechanics

In planetary atmospheres and differentially heated rotating cylindrical tanks (Hide's annulus experiment), poleward temperature gradients establish thermal wind shear according to the Margules equation:
$$\frac{\partial u}{\partial z} = -\frac{g}{f T_0} \frac{\partial T}{\partial y}$$

1. **Baroclinic Instability & Planetary Rossby Waves**:
   When the vertical shear exceeds the critical threshold defined by the Charney-Eady criterion, potential vorticity conservation ($\frac{D q}{Dt} = 0$ on the $\beta$-plane) triggers large-scale baroclinic instability. The circumpolar jet buckles into high-amplitude undulating planetary **Rossby waves** ($m = 5$), which slowly precess eastward at phase velocity:
   $$c = U - \frac{\beta}{K^2}$$

2. **Frontogenesis, Multi-Core Isotachs & Jet-Streak Dynamics**:
   Non-linear ageostrophic convergence sharpens thermal gradients into razor-thin jet ribbons. The jet stream forms concentric nested isotachs (50kt, 100kt, 150kt, 200kt wind speed contours), with intense ageostrophic wind acceleration ("jet streaks") in the diffluent troughs and confluent ridges.

3. **Cut-Off Cyclonic Cold Pools & Polar Vortex Pinwheel**:
   At large wave amplitudes, deep polar troughs pinch off into detached, cold-core cyclonic eddies orbiting the polar periphery. In the cold Arctic core, potential vorticity spiral arms swirl around the central polar vortex, while Kelvin-Helmholtz billows roll along the sheared flanks of the jet stream.

4. **3D Geopotential Relief & Lagrangian Atmospheric Parcel Kinematics**:
   The geopotential height topography is rendered as an iridescent crystalline relief using dual-light Blinn-Phong specular shading, while Lagrangian air-parcel tracers race along the serpentine jet path and recirculate within the cyclonic vortex eyes.

## Visual Composition (60-30-10 Palette)

- **60% Arctic Stratosphere Obsidian Void & Deep Polar Indigo Abyss**: Abyssal vacuum background (`#020308`) and deep subterranean polar vortex indigo (`#080c1e`, `#111632`).
- **30% Baroclinic Jet Ribbons, Glacial Cyan & Sapphire Isotachs**: Serpentine multi-core jet stream filaments and potential vorticity spiral bands (`#0284c7`, `#06b6d4`, `#38bdf8`, `#7dd3fc`).
- **10% Incandescent Jet-Streak Fronts (Diamond-White & Solar Gold)**: Blinding jet-streak wind acceleration fronts (`#ffffff`, `#fef08a`) and warm solar gold cyclonic eye caustics (`#fbbf24`, `#f59e0b`).

## Execution

```bash
uv run python sketch/kinetic_baroclinic_rossby_wave_jet_stream_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_baroclinic_rossby_wave_jet_stream_2d.mp4`)
- Preview snapshot: `kinetic_baroclinic_rossby_wave_jet_stream_2d_p1.png`

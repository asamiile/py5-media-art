# kinetic_rayleigh_plateau_capillary_pinchoff_2d

**kinetic_rayleigh_plateau_capillary_pinchoff_2d** is an algorithmic media art animation simulating the non-linear fluid dynamics of the **Rayleigh-Plateau capillary instability**, **finite-time necking singularities**, and the self-similar **micro-satellite droplet cascade**.

## Concept & Capillary Pinch-Off Dynamics

A cylindrical column of liquid is inherently unstable to axis-symmetric surface perturbations whose wavelength exceeds the jet perimeter ($\lambda > 2\pi R_0$), as driven by Laplace pressure gradients seeking to minimize total surface area.

1. **Non-Linear Capillary Necking & Finite-Time Singularity**:
   As the optimal Rayleigh-Plateau mode ($k \approx 0.697 / R_0$) grows exponentially, curvature gradients pump fluid away from thinning necks into forming droplets. Near the pinch-off threshold, the dynamics transition into the universal self-similar regime (Eggers similarity solution), where the minimum neck radius collapses as a power-law singularity:
   $$h_{\min}(t) \propto (t_c - t)^\alpha$$

2. **Self-Similar Satellite Cascade & End-Pinching**:
   The liquid thread connecting primary drops does not sever at a single point. Instead, secondary capillary necking occurs near the thread ends ("end-pinching"), trapping a tiny micro-thread that collapses into intermediate **satellite** and **sub-satellite** micro-droplets.

3. **Capillary Recoil Ripples & Quadrupole Droplet Oscillations**:
   Upon detachment, the abrupt release of surface tension snaps the severed liquid necks, radiating high-frequency capillary ripples backwards along the drops at capillary phase speed $v_{\text{cap}} = \sqrt{\gamma / \rho R}$. Free primary droplets oscillate dynamically between prolate and oblate spheroids via the Rayleigh quadrupole mode ($m=2$).

4. **3D Specular Liquid Chrome Shading**:
   Liquid interface geometry is evaluated with analytical surface normal vectors $\vec{n} = (-\nabla H, 1) / \|\dots\|$ illuminated by dual light sources (cool glacial azure reflections and warm solar gold caustics) to produce glistening, liquid mercury specular reflections.

## Visual Composition (60-30-10 Palette)

- **60% Cryogenic Vacuum Obsidian Void & Deep Liquid Chromium**: Abyssal vacuum background (`#020206`) and deep liquid chromium core shadows (`#080c18`, `#101828`).
- **30% Oscillating Liquid Mercury & Electric Glacial Cyan**: Glistening fluid jet body and oscillating droplet surfaces (`#06b6d4`, `#38bdf8`, `#0284c7`).
- **10% Incandescent Singularity Pinch-Off Diamond-White & Solar Gold Caustics**: Blinding pinch-off singularity flashes and satellite pearls (`#ffffff`, `#fef08a`, `#fbbf24`), with radial capillary aerosol spray.

## Execution

```bash
uv run python sketch/kinetic_rayleigh_plateau_capillary_pinchoff_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_rayleigh_plateau_capillary_pinchoff_2d.mp4`)
- Preview snapshot: `kinetic_rayleigh_plateau_capillary_pinchoff_2d_p1.png`

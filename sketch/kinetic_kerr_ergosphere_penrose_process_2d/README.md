# kinetic_kerr_ergosphere_penrose_process_2d

**kinetic_kerr_ergosphere_penrose_process_2d** is an algorithmic media art animation simulating general relativistic spacetime dynamics around a rotating **Kerr black hole**, capturing the **Lense-Thirring frame-dragging effect**, the oblate geometry of the **ergosphere static limit**, extreme **relativistic Doppler beaming and gravitational redshift**, and rotational energy extraction via the **Penrose process**.

## Concept & Relativistic Kerr Spacetime Mechanics

In Albert Einstein's General Relativity, a stationary, axisymmetric rotating black hole of mass $M$ and specific angular momentum $a = J/M$ is described by the Kerr metric in Boyer-Lindquist coordinates:

$$ds^2 = -\left(1 - \frac{2Mr}{\Sigma}\right) dt^2 - \frac{4Mar\sin^2\theta}{\Sigma} dt d\phi + \frac{\Sigma}{\Delta} dr^2 + \Sigma d\theta^2 + \left(r^2 + a^2 + \frac{2Ma^2r\sin^2\theta}{\Sigma}\right)\sin^2\theta d\phi^2$$

where $\Sigma = r^2 + a^2 \cos^2\theta$ and $\Delta = r^2 - 2Mr + a^2$.

- **Outer Event Horizon & Ergosphere**:
  The event horizon occurs where $\Delta = 0$ ($r_+ = M + \sqrt{M^2 - a^2}$). Outside the horizon lies the oblate **ergosphere**, bounded by the static limit surface where $g_{tt} = 0$:
  $$r_E(\theta) = M + \sqrt{M^2 - a^2 \cos^2\theta}$$
  Inside the ergosphere, the dragging of spacetime by the spinning singularity exceeds the speed of light ($c$), making it physically impossible for any particle or light ray to remain static relative to an observer at infinity.
- **Lense-Thirring Frame Dragging**:
  The angular velocity of zero-angular-momentum observers (ZAMOs) drags spacetime at rate $\omega_{LT}(r, \theta) = -g_{t\phi}/g_{\phi\phi}$, twisting infalling matter into tight relativistic spirals.
- **Relativistic Beaming & Gravitational Redshift**:
  Accreting plasma swirling towards the observer experiences intense kinematic Doppler beaming $\delta = [\gamma (1 - \beta \cos \phi)]^{-1}$, creating a stark asymmetry: the approaching side radiates with searing electric cyan incandescence, while the receding side is dimmed and gravitationally redshifted into deep crimson and violet.
- **The Penrose Process**:
  Infalling particles crossing the static limit break apart into twin fragments. One daughter particle falls into the event horizon on a negative-energy orbit relative to infinity, while the escaping daughter particle is flung outward with kinetic energy exceeding that of the original parent, directly tapping and extracting the black hole's irreducible rotational mass-energy.

## Visual Composition (60-30-10 Palette)

- **60% Event Horizon Singularity Obsidian & Redshifted Crimson/Violet**: Pitch black gravitational shadow (`#010206`) and deeply redshifted receding disk matter (`#4c0519`, `#2e1065`).
- **30% Relativistically Blueshifted Cyan & Celestial Mint**: Blueshifted approaching accretion crescent (`#06b6d4`, `#10b981`) and glowing ergosphere static limit contours (`#00f0ff`).
- **10% Incandescent Penrose Beaming Gold & Pure White**: Relativistic axial jets (`#fef08a`), photon orbit ring, and boosted escaping Penrose particles (`#ffffff`).

## Execution

```bash
uv run python sketch/kinetic_kerr_ergosphere_penrose_process_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_kerr_ergosphere_penrose_process_2d.mp4`)
- Preview snapshot: `kinetic_kerr_ergosphere_penrose_process_2d_p1.png`

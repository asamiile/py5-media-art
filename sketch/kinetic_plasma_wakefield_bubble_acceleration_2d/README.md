# kinetic_plasma_wakefield_bubble_acceleration_2d

**kinetic_plasma_wakefield_bubble_acceleration_2d** is an algorithmic media art animation simulating relativistic laser-plasma wakefield acceleration in the non-linear **blowout / bubble regime**. The piece models **ponderomotive electron cavitation**, **multi-gigavolt/meter longitudinal accelerating fields ($E_z$)**, **linear transverse focusing forces ($W_\perp$)**, **relativistic electron sheath dynamics**, **serpentine betatron oscillations**, and **forward-beamed synchrotron radiation emission**.

## Concept & Relativistic Wakefield Physics

When an ultra-short, high-intensity laser pulse ($a_0 > 2$) or dense relativistic particle bunch propagates through an underdense plasma, the massive **ponderomotive force** ($\vec{F}_p = -\frac{m c^2}{4\gamma} \nabla a_0^2$) expels nearly all background electrons radially outward away from the laser propagation axis.

1. **The Blowout / Bubble Cavity**:
   Because the massive positive ions remain virtually stationary on the femtosecond laser timescale, a spherical cavity devoid of electrons—a **bare ion bubble**—is formed trailing the laser front.
2. **Relativistic Electron Sheath & Rear Cusp**:
   The expelled electrons form a dense, curved boundary layer (the sheath) around the bubble surface. As they curve around the bubble equator, the space-charge of the ion core pulls them violently back toward the axis, where they focus into an ultra-dense cusp at the rear vertex ($\xi \approx \xi_c - R_B$).
3. **Multi-GV/m Accelerating Electric Field ($E_z$)**:
   Inside the bubble, the positive ion background produces a co-moving electrostatic field with a steep linear gradient:
   $$E_z(\xi) \propto \frac{m c \omega_p}{e} \frac{k_p}{2}(\xi - \xi_c)$$
   The rear half of the bubble provides an enormous longitudinal accelerating gradient exceeding $100\text{ GV/m}$, accelerating trapped witness electrons to relativistic multi-GeV energies across millimeter distances.
4. **Transverse Focusing & Betatron Radiation**:
   According to the Panofsky-Wenzel theorem, the radial space-charge field combined with the azimuthal magnetic field produces a linear restoring force $W_\perp(r) = E_r - c B_\theta = -\frac{m \omega_p^2}{2e} r$. Trapped electrons execute rapid serpentine **betatron oscillations** ($\omega_\beta = \omega_p / \sqrt{2\gamma}$), emitting intense forward-beamed synchrotron x-ray radiation fans.

## Visual Composition (60-30-10 Palette)

- **60% Relativistic Vacuum Obsidian & Ion Cavity Cobalt/Indigo**: Deep cosmic vacuum (`#010206`) and bare ion channel interior (`#081026`, `#141d36`).
- **30% Relativistic Electron Sheath Cyan & Ozone Blue**: High-density electron sheath boundary, laser optical cycles, and secondary plasma wake cavities (`#00f0ff`, `#38bdf8`, `#0284c7`).
- **10% Accelerated Witness Bunch White-Gold & Betatron Synchrotron Violet**: Incandescent trapped electron bunch (`#ffffff`, `#fef08a`, `#f59e0b`) and forward-beamed betatron synchrotron radiation arcs (`#e879f9`, `#c084fc`).

## Execution

```bash
uv run python sketch/kinetic_plasma_wakefield_bubble_acceleration_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_plasma_wakefield_bubble_acceleration_2d.mp4`)
- Preview snapshot: `kinetic_plasma_wakefield_bubble_acceleration_2d_p1.png`

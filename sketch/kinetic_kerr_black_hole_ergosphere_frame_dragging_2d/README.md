# kinetic_kerr_black_hole_ergosphere_frame_dragging_2d

**Genre**: Astronomical / Relativistic Astrophysics / General Relativity  
**Format**: 4K UHD (3840×2160), 60 fps, 720 frames (12.0s seamless harmonic loop)  
**Palette**: Deep Interstellar Obsidian (`#020409`), Electric Cyan (`#38bdf8`), Diamond White (`#f8fafc`), Neon Emerald (`#10b981`), Radiant Amber (`#f59e0b`), Incandescent Copper (`#ea580c`), Deep Garnet Crimson (`#991b1b`), Relativistic Purple (`#a855f7`)

---

## Concept & Mathematical Formulation

*Kinetic Kerr Black Hole Ergosphere Frame Dragging 2D* is an autonomous generative media artwork celebrating relativistic astrophysics and general relativity, visualizing Roy Kerr's 1963 exact stationary axisymmetric vacuum solution to Albert Einstein's field equations:

$$G_{\mu\nu} = 0$$

Describing the spacetime geometry surrounding an uncharged, rapidly rotating black hole ($a^* = 0.940$). In Boyer-Lindquist coordinates $(t, r, \theta, \phi)$, the metric line element reads:

$$ds^2 = -\left(1 - \frac{2Mr}{\rho^2}\right) dt^2 - \frac{4aMr\sin^2\theta}{\rho^2} dt\,d\phi + \frac{\rho^2}{\Delta} dr^2 + \rho^2 d\theta^2 + \left(r^2 + a^2 + \frac{2Ma^2r\sin^2\theta}{\rho^2}\right)\sin^2\theta\,d\phi^2$$

where $\rho^2 = r^2 + a^2\cos^2\theta$ and $\Delta = r^2 - 2Mr + a^2$.

### Key Relativistic Features
1. **Event Horizon ($r_+$)**: The outer null boundary at $r_+ = M + \sqrt{M^2 - a^2} \approx 1.341 M$, beyond which no signal can escape.
2. **Static Limit Ergosphere ($r_E$)**: The oblate boundary $r_E(\theta) = M + \sqrt{M^2 - a^2\cos^2\theta}$ where $g_{tt} = 0$. Outside the horizon but within the ergosphere, the frame-dragging (Lense-Thirring effect) is so extreme that spacetime itself is dragged faster than light along the direction of rotation.
3. **Penrose Process Energy Extraction**: Rotational energy ($E_{\text{rot}} \approx 0.29 M$) can be extracted with up to $\eta_{\text{max}} = 20.7\%$ efficiency from negative-energy states inside the ergosphere.
4. **Relativistic Doppler Beaming**: Radiation from the Novikov-Thorne thin accretion disk orbiting at prograde relativistic Keplerian velocities ($v \sim 0.3c - 0.7c$) experiences Doppler beaming $\delta = 1 / [\gamma(1 - v_{\parallel}/c)]$, shifting observed flux by $\delta^{3+\alpha}$. The approaching limb blazes in intense electric cyan and diamond white, while the receding limb shifts into deep amber, copper, and garnet crimson.
5. **Gravitational Lensing Halo (Luminet-Thorne Ray Tracing)**: Light from the rear of the disk passing over the top of the hole is strongly deflected by gravitational lensing, forming a majestic circular canopy arching above the shadow void and converging gracefully with the equatorial disk tips.
6. **Blandford-Znajek Relativistic Jets**: Magnetic flux ropes threading the spinning ergosphere extract rotational energy, launching collimated plasma jets along the polar axis with helical magnetic field lines.

---

## Archival Relativistic Telemetry Layout

Presented as an archival astrophysics observatory telemetry display on deep obsidian canvas (`#020409`):
- **Boyer-Lindquist Geodesic Graticule**: Subtle concentric coordinate spheres and polar geodesics framing the black hole.
- **Asymmetric Kerr Shadow Void**: The flattened Bardeen shadow silhouette shifted by frame dragging ($dx = 0.14 a^* M$) with a razor-sharp caustic photon ring.
- **Four Relativistic Telemetry Apparatus Cards**:
  - *Top-Left*: Boyer-Lindquist Kerr Metric Tensor and horizon radius telemetry ($r_+ = 1.341 M, r_E, r_{\text{isco}}$).
  - *Top-Right*: Relativistic Doppler Beaming intensity profile curve, Lorentz factor $\gamma_{\text{max}} = 1.48$, and flux asymmetry ratio ($8.6 : 1$).
  - *Bottom-Left*: Penrose Process Energy Extraction kinematics showing negative-energy particle trajectory and escaping boosted quantum.
  - *Bottom-Right*: Kerr Spin parameter $a^* = 0.940$, horizon angular velocity $\Omega_H$, and Blandford-Znajek jet power monitor.
- **Strict Anonymity**: Clean archival drafting borders and Latin typography, strictly free of artist signatures, initials, or seals (落款).

---

## Execution & Output

```bash
uv run python sketch/kinetic_kerr_black_hole_ergosphere_frame_dragging_2d/main.py
```

- **Preview**: `kinetic_kerr_black_hole_ergosphere_frame_dragging_2d_p1.png`
- **Animation**: `output.mp4` (H.264, 4K 60fps, 720 frames, 12.0s seamless loop)

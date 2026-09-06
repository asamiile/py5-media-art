# kinetic_optical_vortex_phase_singularities_2d

**kinetic_optical_vortex_phase_singularities_2d** is an algorithmic media art animation exploring the singular optics and topological wave mechanics of **Laguerre-Gaussian (LG) laser beams**, quantized **Orbital Angular Momentum (OAM)**, and moving **phase singularities**.

## Concept & Physics

An optical vortex is a light beam whose wavefront possesses a helical dislocation. At the center of the helix, the phase is undefined (a phase singularity), requiring the optical field intensity to strictly vanish:

$$E_{\text{total}}(\mathbf{r}, t) = E_0(\mathbf{r}) \prod_{k=1}^N \left( (x - x_k(t)) + i \cdot \text{sgn}(\ell_k) (y - y_k(t)) \right)^{|\ell_k|}$$

- **Topological Charges ($\ell \in \{+2, -3, +1, -1\}$)**: Each vortex carries an orbital angular momentum of $\ell \hbar$ per photon. Around each singularity, the optical phase winds by $2\pi \ell$.
- **Helical Equiphase Fan Braids**: Constant-phase lines form intricate multi-polar spiral petals that continuously twist, braid, and reconnect as the vortices execute non-linear orbital choreographies.
- **Holographic Fork Dislocations**: Interference with a tilted spherical reference wave reproduces real-world interferometric diagnostic patterns, revealing iconic fork dislocations where fringes bifurcate into $\ell$ prongs.
- **Transverse Poynting Vector Flow & Optical Tweezers**:
  $$\mathbf{S}_{\perp} \propto \operatorname{Im}(\psi^* \nabla \psi)$$
  The energy circulation exerts radiation torque on microscopic dielectric nanoparticles, trapping them in glowing planetary orbits around the dark vortex eyes.

## Visual Composition (60-30-10 Palette)

- **60% Abyssal Obsidian & Midnight Space**: Deep obsidian and Prussian midnight void (`#02040d`, `#0b1428`) framing dark interference nulls and vortex cores.
- **30% Holographic Cyan & Prismatic Magenta**: Luminous electric cyan (`#06b6d4`, `#22d3ee`) interference fringes and radiant fuchsia/magenta (`#ec4899`, `#d946ef`) helical equiphase braids.
- **10% Incandescent Solar Gold & Diamond White**: Radiant solar amber (`#f59e0b`), molten gold (`#fbbf24`), and diamond-white (`#ffffff`) optical vortex singularity halos and trapped dielectric photon tracer particles.

## Execution

```bash
uv run python sketch/kinetic_optical_vortex_phase_singularities_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_optical_vortex_phase_singularities_2d.mp4`)
- Preview snapshot: `kinetic_optical_vortex_phase_singularities_2d_p1.png`

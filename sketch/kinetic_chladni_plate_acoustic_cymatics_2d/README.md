# kinetic_chladni_plate_acoustic_cymatics_2d

**kinetic_chladni_plate_acoustic_cymatics_2d** is an algorithmic media art animation simulating the acoustic physics and vibrational cymatics of **Chladni figures on a circular elastic plate**, modeling continuous eigenmode frequency sweeps, dynamic nodal line bifurcations, and the collective avalanching of fluorescent sand particles toward zero-acceleration nodal lines.

## Concept & Acoustical Physics

When a thin elastic plate is driven into transverse vibration by an acoustic transducer at resonant natural frequencies $\omega_{m,n}$, the out-of-plane displacement field $W(r, \theta, t)$ forms standing wave eigenmodes:

$$W(r, \theta, t) = \sum_{j} A_j R_{m_j, k_j}(r) \cos(m_j \theta - \phi_j(t)) \cos(\omega_j t)$$

- **Bessel-Fourier Radial Standing Waves**:
  In polar coordinates, radial wave amplitudes are governed by Bessel functions $J_m(k r)$, while azimuthal modes produce $m$-fold rotational symmetries. Interferences between orthogonal degenerate modes produce concentric rings, radial spokes, and hyperbolic saddle loops.
- **Continuous Resonant Frequency Sweeps**:
  As the acoustic driving frequency sweeps dynamically, the eigenmode parameters $(m_1, k_1, m_2, k_2)$ transition smoothly, causing existing nodal lines to split, reconnect, and metamorphose into higher-order geometric mandalas.
- **Acoustic Radiation Force & Sand Avalanches**:
  Particles of sand or lycopodium powder resting on the vibrating plate experience an effective acoustic radiation drift force proportional to the negative gradient of vibrational kinetic energy:
  $$\mathbf{F}_{\text{drift}} \propto - \nabla \langle W^2 \rangle$$
  Sand grains are kicked violently away from energetic antinodes and gravitate into dense, crystalline filaments along the quiescent **nodal lines ($W = 0$)**.
- **Framed Circular Anodized Plate**:
  A dark brushed carbon-composite circular plate bounded by an incandescent polished brass rim provides rich material contrast against the glowing cymatics figures.

## Visual Composition (60-30-10 Palette)

- **60% Anodized Carbon-Composite Plate Base**: Dark matte acoustic obsidian (`#020308`, `#060a18`) framed by a polished brass rim (`#e1b12c`, `#f5cd79`).
- **30% Nodal Line Sand Filaments & Antinode Glow**: Luminous Electric Cyan (`#00f5d4`) and Mint Emerald (`#00bbf9`) tracing the zero-acceleration nodal curves, complemented by a subtle Royal Amethyst (`#7209b7`, `#3a0ca3`) antinode kinetic vibration halo.
- **10% High-Density Nodal Intersections & Sand Grains**: Radiant Solar Gold (`#ffd166`) and pure Diamond White (`#ffffff`) marking modal intersections and avalanching fluorescent sand crystals.

## Execution

```bash
uv run python sketch/kinetic_chladni_plate_acoustic_cymatics_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_chladni_plate_acoustic_cymatics_2d.mp4`)
- Preview snapshot: `kinetic_chladni_plate_acoustic_cymatics_2d_p1.png`

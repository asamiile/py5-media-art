# kinetic_topological_edge_magnetoplasmon_2d

**kinetic_topological_edge_magnetoplasmon_2d** is an algorithmic media art animation simulating the topological electrodynamics of **chiral Edge Magnetoplasmons (EMPs)** and **cyclotron skipping orbits** in a mesoscopic **2D Electron Gas (2DEG)** under the Integer Quantum Hall Effect.

## Concept & Topological Quantum Hall Dynamics

In a two-dimensional electron gas subjected to a strong perpendicular magnetic field $B_\perp$ at low temperatures, the bulk electron spectrum collapses into discrete, highly degenerate **Landau levels**:
$$E_n = \hbar \omega_c \left(n + \frac{1}{2}\right)$$
where $\omega_c = e B_\perp / m^*$ is the cyclotron frequency.

1. **Topological Edge States & Time-Reversal Symmetry Breaking**:
   In the bulk, the Fermi energy lies in the mobility gap between Landau levels, making the interior an incompressible topological insulator. Near the physical boundary, the confining electrostatic potential $V_{conf}(r)$ bends the Landau levels upward across the Fermi energy, creating gapless, unidirectional **chiral topological edge channels**.
2. **Chiral Edge Magnetoplasmons (EMPs)**:
   Acoustic collective charge-density waves propagate strictly unidirectionally (clockwise) along the sample perimeter with dispersion:
   $$\omega(q) \sim \frac{2 \sigma_{xy}}{\epsilon} q \ln\left(\frac{1}{|q| d}\right)$$
   Time-reversal symmetry is broken by $B_\perp$, ensuring that EMPs bypass non-magnetic boundary defects without backscattering.
3. **Quantum Point Contact (QPC) & Aharonov-Bohm Interferometry**:
   At a narrow constriction (QPC), upper and lower chiral edge channels approach within a magnetic length $l_B = \sqrt{\hbar / e B}$, allowing coherent quantum tunneling. Electrons partition into transmitted and reflected paths, creating an electronic Mach-Zehnder interferometer with periodic Aharonov-Bohm phase interference fringes:
   $$\Delta \theta_{AB} = 2\pi \frac{\Phi_B}{\Phi_0}$$
4. **Chiral Skipping Orbits**:
   Electrons in the bulk execute closed circular cyclotron orbits. When an orbit collides with the steep confining potential at the droplet perimeter, the boundary specularly reflects the electron, producing rolling **cycloidal skipping orbits** that travel clockwise along the perimeter at drift velocity $v_D = (\nabla V \times \vec{B}) / B^2$.

## Visual Composition (60-30-10 Palette)

- **60% Cryogenic Obsidian Void & Bulk Landau Indigo**: Cryogenic dilution refrigerator vacuum (`#01030a`) and incompressible bulk Landau level interior (`#081226`, `#121e3c`).
- **30% Chiral Topological Edge Electric Cyan & Emerald Mint**: Unidirectional EMP charge-density wave ribbon and topological edge channels (`#00f0ff`, `#10b981`, `#06b6d4`).
- **10% QPC Tunneling Solar Gold & Aharonov-Bohm Phase Violet**: Coherent quantum point contact tunneling junction (`#ffffff`, `#fbbf24`) and Aharonov-Bohm interferometric phase fringes (`#e879f9`, `#c084fc`).

## Execution

```bash
uv run python sketch/kinetic_topological_edge_magnetoplasmon_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_topological_edge_magnetoplasmon_2d.mp4`)
- Preview snapshot: `kinetic_topological_edge_magnetoplasmon_2d_p1.png`

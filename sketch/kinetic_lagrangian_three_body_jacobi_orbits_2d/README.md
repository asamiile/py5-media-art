# kinetic_lagrangian_three_body_jacobi_orbits_2d

Kinetic Circular Restricted Three-Body Problem (CR3BP) and Jacobi invariant manifold topology simulation executed in py5.

## Concept

An artistic exploration of celestial mechanics, astrodynamics, and chaotic orbital transport, inspired by the mathematical formulations of Joseph-Louis Lagrange and Carl Gustav Jacob Jacobi.

In the non-inertial rotating frame of two gravitationally bound celestial bodies—a radiant Primary star and an orbiting ringed gas giant—the balance between gravitational pull and centrifugal acceleration establishes five equilibrium libration points ($L_1, L_2, L_3, L_4, L_5$). The effective potential field (Roche potential):

$$U(x, y) = \frac{1}{2}(x^2 + y^2) + \frac{1-\mu}{r_1} + \frac{\mu}{r_2}$$

defines zero-velocity boundary contours where test particles can move for a given Jacobi Constant $C_J = 2U(x, y) - v^2$. The artwork simulates 21 continuous equipotential curves connecting through the critical neck at $L_1$, flowing invariant manifold stream ribbons ("The Interplanetary Superhighway") linking interior and exterior planetary space, periodic Lyapunov and Halo orbits, and resonant Trojan asteroid swarms orbiting $L_4$ and $L_5$ across deep cosmic obsidian space.

## Technical Details

- **Resolution**: 3840×2160 (4K UHD)
- **Duration**: 720 frames @ 60 FPS (12.0s seamless $C^1$ loop)
- **Genre Taxonomy**: Astronomical / Celestial Mechanics / Astrodynamics
- **Astrodynamics & Mathematical Modeling**:
  - Roche Potential Contours: 21 exact isopotential curves computed on a computational grid ($960 \times 540$) and extracted via OpenCV high-precision polygonal contour tracing, spanning the triangular $L_4/L_5$ absolute minima ($U \approx 1.44$) up to steep stellar gravitational funnels ($U = 4.60$).
  - Critical Roche Lobe Neck: Visualizes the figure-eight separatrix topology passing through $L_1$ and $L_2$, demonstrating orbital exchange gateways.
  - Invariant Manifold Tubes: 44 parametric stream ribbons ($A(s) \sin(\omega t + ks)$) modeling the stable/unstable manifold tubes that enable ballistic lunar and interplanetary transfers.
  - Outer Escape Plume: 24 hyperbolic dispersal streamlines radiating from $L_2$ into deep interstellar space.
  - Periodic Orbits: 5-tier nested Lyapunov and Halo orbit families oscillating around $L_1$ and $L_2$.
  - Trojan Libration Swarms: 10-tier nested tadpole and horseshoe orbits around the triangular libration points $L_4$ and $L_5$ populated by 28 orbiting asteroid particulates.
- **Palette & Radiance**:
  - Ground: Deep Interstellar Obsidian Void (`#07090f`) with twinkling background starfield.
  - Primary Star: Solar Amber (`#f59e0b`), Radiant Corona (`#fef08a`), and Specular White core (`#ffffff`).
  - Secondary Planet: Cobalt Blue (`#2563eb`), Glacial Cyan Ring System (`#93c5fd`), and Cerulean atmosphere (`#60a5fa`).
  - Potential Contours: Deep Celestial Indigo (`#2655aa`), Electric Cyan (`#26b9f0`), Solar Amber Gold (`#e0a020`), and Laser Rose-Crimson (`#f43f5e`).
  - Telemetry: Astrometric graticule, millimeter coordinate scale, and rotating True Anomaly Astrolabe dial.
- **Anonymity**: 100% autonomous algorithmic generative art without human authorship marks, signatures, or name seals.

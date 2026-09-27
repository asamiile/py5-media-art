# kinetic_plasmoid_instability_magnetic_reconnection_2d

2D generative media art depicting the spontaneous breakdown of a Sweet-Parker reconnecting current sheet into a dynamic cascading chain of plasmoids (magnetic islands) via the tearing-mode plasmoid instability at extreme Lundquist numbers ($S \gg 10^4$).

## Physics & Generative Concept

Magnetic reconnection is a fundamental astrophysical process wherein antiparallel magnetic field lines rapidly break and topologically reconnect, converting vast reservoirs of magnetic energy into explosive plasma thermal and kinetic energy (such as in solar flares, geomagnetic substorms, and tokamak disruptions).

Classical Sweet-Parker reconnection predicts an extremely slow reconnection rate scaling as $S^{-1/2}$, which fails to explain the observed explosive timescales in nature. Modern resistive and Hall-MHD theory reveals that when the Lundquist number exceeds a critical threshold ($S_c \sim 10^4$), the Sweet-Parker current sheet becomes violently unstable to secondary tearing modes:

1. **Current Sheet Breakdown & Plasmoid Chain**: The elongated central current sheet shatters into hierarchical secondary magnetic islands (plasmoids) separated by secondary $X$-points.
2. **Coalescence Instability**: Neighboring plasmoids attract and coalesce via the coalescence instability, growing into "monster plasmoids" that accelerate towards the exhaust exits at the Alfvén speed $v_A$.
3. **Hall-MHD Quadrupolar $B_z$ Field**: In the sub-ion diffusion region where electrons and ions decouple, Hall currents produce a characteristic 4-lobed out-of-plane magnetic field $B_z$ with alternating polarities around each reconnection $X$-point.
4. **Kinetic Particle Acceleration**: Charged particles experience $\mathbf{E} \times \mathbf{B}$ drift towards the reconnection layer with Larmor gyration, followed by explosive lateral ejection into the Alfvénic exhaust jets.

## Technical Implementation

- **Vector Potential Formulation**: Continuous 2D magnetic flux function $A_z(x, y)$ on a high-density computational grid ($480 \times 270$), parameterized by Harris sheet equilibria and secondary tearing Fourier modes.
- **MHD Field Operators**: Numerical differentiation yields exact magnetic vector components $B_x = -\partial A_z / \partial y$, $B_y = \partial A_z / \partial x$, and out-of-plane current density $J_z = -\nabla^2 A_z$.
- **Normal Mapping & Dual Specular Highlights**: Dynamic surface gradients shaded by two directional light vectors, illuminating the reconnected flux ropes and sharp current spikes.
- **Particle System**: 3,800 relativistic plasma particles tracked through multi-stage inflow, gyro-motion, and Alfvénic outflow jets.
- **Format**: 900 frames @ 60 FPS (15 seconds seamless loop) rendered at 1920×1080 via py5 P2D with ffmpeg H.264 master encoding.

## Color Palette

- **Inflow Field Manifolds & Streamlines**: Deep Obsidian Void (`#01030a`), Deep Sapphire Blue (`#020b24`), and Glacial Cyan (`#00e5ff`).
- **Ohmic Dissipation & Current Sheets**: Incandescent Solar Flare Amber (`#ff8800`) and Radiant Gold (`#ffea00`).
- **Plasmoid Cores & Quadrupole Lobes**: Hyper Laser Magenta (`#ff0066`), Ionized Violet (`#7700ff`), and Cerulean Turquoise (`#00ffbb`).
- **Specular $X$-Point Sparks**: Pure Diamond White (`#ffffff`).

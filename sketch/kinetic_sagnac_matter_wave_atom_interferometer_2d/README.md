# kinetic_sagnac_matter_wave_atom_interferometer_2d

2D generative media art depicting coherent matter-wave de Broglie wavepacket splitting, redirection, and recombination in a Mach-Zehnder cold-atom interferometer, sensing rotation via the quantum Sagnac effect ($\Delta \Phi = \frac{4 m}{\hbar} \boldsymbol{\Omega} \cdot \mathbf{A}$).

## Physics & Generative Concept

Matter-wave interferometry harnesses the quantum wave-particle duality of matter. Because the de Broglie wavelength of an atom $\lambda_{\text{dB}} = h / (m v)$ is associated with massive particles ($m \gg 0$), atom interferometers exhibit an extraordinary sensitivity to inertial forces (rotations, accelerations, and gravitational curvature) that is orders of magnitude greater than optical photon interferometers:

1. **Bragg Pulse Beam-Splitters & Mirrors**: Retro-reflected counter-propagating laser beams create optical standing wave lattices. A $\pi/2$ pulse coherently splits an incoming Bose-Einstein condensate cloud into two momentum states ($|p=0\rangle$ and $|p=2\hbar k_L\rangle$). At the apex, a $\pi$ pulse reverses the relative momenta, acting as a quantum mirror. A final $\pi/2$ pulse recombines the wavepackets.
2. **Mach-Zehnder Diamond Trajectory**: The two wavepackets trace a closed geometric area $\mathbf{A}$ in spacetime, bounding an enclosed quantum phase loop.
3. **Quantum Sagnac Effect**: In a rotating frame with angular velocity $\boldsymbol{\Omega}$, the relativistic and kinematic phase shift accumulated along the loop is $\Delta \Phi = \frac{4 m}{\hbar} \boldsymbol{\Omega} \cdot \mathbf{A}$.
4. **Quantum Interference Fringes**: Upon recombination, constructive and destructive interference alternates probability density between output ports, generating spatial and temporal matter-wave interference fringes.

## Technical Implementation

- **Wavefunction & Carrier Modeling**: Continuous 2D quantum matter-wave field $\Psi(x, y, t) = \psi_1 + \psi_2$ on a $480 \times 270$ numerical grid with de Broglie carrier waves, Gaussian wavepacket envelopes, and quantum phase winding $\arg(\Psi)$.
- **Optical Lattice Modulation**: Pulsed retro-reflected vertical laser beams with standing-wave spatial node modulation ($\cos^2(k_L y)$).
- **Dual-Light Specular Shading**: Cryogenic vacuum chamber optics illuminated by two directional lights, creating iridescent chrome quantum reflections.
- **Particle System**: 3,600 laser-cooled Rubidium-87 atoms traversing ballistic matter-wave geodesics, scattering fluorescent photons at Bragg interaction nodes and partitioning into output ports according to $\cos^2(\Delta \Phi / 2)$.
- **Format**: 900 frames @ 60 FPS (15 seconds seamless loop) rendered at 1920×1080 via py5 P2D with ffmpeg H.264 master encoding.

## Color Palette

- **Optical Bragg Laser Beams**: Fluorescent Laser Emerald (`#00ff77`) and Electric Mint (`#20ffa5`).
- **Matter-Wave Cores & Guides**: Electric Glacial Cyan (`#00e5ff`) and Sapphire Blue (`#0033aa`).
- **Quantum Phase Interference**: Neon Laser Magenta (`#ff0088`) and Royal Amethyst Violet (`#7700ff`).
- **Sagnac Output Interference Fringes**: Incandescent Solar Gold (`#ffea00`).
- **Specular Chamber Optics**: Liquid Diamond White (`#ffffff`).
- **Cryogenic Ultra-High Vacuum Void**: Midnight Obsidian (`#010208`).

# soliton_resonance_void

- **Theme**: Nonlinear Schrödinger Equation (NLSE), solitons, breather modes, wave interference.
- **Technique**: 2D NLSE simulation on a 256x256 grid using finite difference methods. Visualizes the evolution and collision of multiple localized wave packets (solitons) in a focusing nonlinear medium. Intensity mapping to height and color.
- **Palette**: "Deep Violet / Neon Rose / Electric Gold".
- **Description**: A dark, tranquil pool of violet energy where bright, localized pulses of rose and gold light emerge, collide, and pass through each other with intense, flickering resonance, demonstrating the unique stability and interaction of solitons.

## Technical Details

- **Simulation**: 2D Nonlinear Schrödinger Equation (NLSE): $i \psi_t = -0.5 \nabla^2 \psi - \gamma |\psi|^2 \psi$.
- **Dynamics**: Multiple initial Gaussian wave packets with momentum evolve, collide, and interfere.
- **Rendering**: P3D surface rendering using `TRIANGLE_STRIP` on a 256x256 complex field.
- **Output**: 4K/60fps MP4.

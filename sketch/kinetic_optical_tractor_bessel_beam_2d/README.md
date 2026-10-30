# kinetic_optical_tractor_bessel_beam_2d

2D wave optics and photonics simulation depicting structured singular optics, non-diffracting high-order Bessel-vortex beams, negative radiation pressure, and retrograde optical tractor pulling dynamics.

## Concept & Physics

In structured optical fields, non-diffracting beams can exert a counter-intuitive **negative radiation pressure**, pulling microscopic dielectric particles upstream toward the laser light source against the direction of wave propagation:
1. **High-Order Bessel-Vortex Beam**: A monochromatic light field carrying orbital angular momentum (topological charge $m = 2$) is described by the radial Bessel profile $E(r, \theta, z) \propto J_2(k_r r) e^{i(2\theta + k_z z - \omega t)}$, forming concentric non-diffracting cylindrical intensity shells with a central dark phase singularity.
2. **Optical Gradient Force**: Dielectric particles experience a strong transverse gradient force $\mathbf{F}_{\text{grad}} \propto \nabla |E|^2$ that traps them securely onto the bright concentric Bessel rings ($r \approx 0.82, 1.65, 2.45, 3.25$).
3. **Negative Radiation Force (Optical Pulling)**: Because of the conical wavevector spectrum and enhanced backward scattering interference, conservation of axial momentum imparts negative momentum to the trapped particles, pulling them backward along $-z$ toward the focal emission aperture.
4. **Orbital Angular Momentum Torque**: The vortex phase gradient imparts an azimuthal torque, driving particles into 3D-projected helical corkscrew trajectories as they spiral into the glowing aperture throat.
5. **Lagrangian Kinematics**: 2,400 particles showcase the paradox: golden matter particles being reeled backward into the aperture against forward-propagating electric mint photon wavepackets.

## Aesthetics & Color Palette

- **Optical Aperture & Axial Singularity**: Blinding Laser Core Liquid Diamond White (`#ffffff`)
- **Bessel Diffraction Rings**: Radiant Laser Emerald & Electric Mint (`#00e676` to `#00b0ff`)
- **Pulled Matter Sparks & Spiral Trajectories**: Solar Amber & Topaz Gold (`#ffab00` to `#ffd740`)
- **Forward Light Pulses**: Fluorescent Pale Mint (`#d2ffe6`)
- **Cosmic Void**: Deep Indigo Obsidian (`#060910`)

## Specifications

- **Format**: Seamless looping animation (720 frames @ 60 FPS, 12 seconds)
- **Resolution**: 1920×1080 (HD preview) / 3840×2160 (4K master)
- **Engine**: py5 (Python Processing) + SciPy analytical Bessel functions + NumPy vectorized field tensor synthesis + Blinn-Phong dual-light specular normal mapping + vectorized batch trail rendering (`py5.lines()`, `py5.points()`)

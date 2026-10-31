# kinetic_binary_gravitational_microlensing_caustics_2d

2D relativistic astrophysics simulation of binary gravitational microlensing, depicting the complex 2-body lens equation, critical curves where the Jacobian determinant vanishes ($\det J = 0$), astroid-shaped caustic networks, extreme relativistic magnification spikes ($A \propto 1 / |\det J|$), and multi-image creation/annihilation kinematics.

## Concept & Physics

In gravitational microlensing, when a distant background light source aligns with a binary star or star-planet system, light rays are deflected non-linearly according to general relativity:
1. **Complex Binary Lens Equation**: The mapping between the lens plane $z = x + iy$ and the source plane $w = u + iv$ is given by:
   $$w = z - \frac{m_1}{\bar{z} - \bar{z}_1} - \frac{m_2}{\bar{z} - \bar{z}_2}$$
   where $m_1, m_2$ are the normalized lens masses and $z_1, z_2$ are their instantaneous positions.
2. **Critical Curves & Caustics**: Critical curves are closed contours in the lens plane where the Jacobian determinant vanishes ($\det J = 1 - |\gamma|^2 = 0$, where $\gamma$ is the complex gravitational shear). These map onto singular caustic curves (fold lines and sharp cusps) in the source plane.
3. **Relativistic Magnification Catastrophe**: As a source approaches and crosses a fold caustic, the magnification diverges ($A \propto 1 / \sqrt{\Delta u}$), causing intense flaring and the spontaneous creation or annihilation of a pair of bright relativistic images.
4. **Spacetime Curvature Shading**: Dual-light Blinn-Phong specular relief normal mapping visually sculpts the deep gravitational potential well $\Phi(x, y) = \frac{1}{2}(m_1 \ln r_1^2 + m_2 \ln r_2^2)$ and caustic ridges.
5. **Lagrangian Photon Kinematics**: 2,400 photon rays stream across the binary field; unperturbed rays glide in glacial cyan, while photons traversing the caustic boundary ignite into blazing solar gold and diamond-white focal plumes.

## Aesthetics & Color Palette

- **Spacetime Fabric Void**: Deep Obsidian Space Abyss (`#020409`)
- **Gravitational Potential Wells**: Midnight Sapphire & Deep Indigo (`#0c142e` to `#1e3a8a`)
- **Critical Curve Boundaries**: Radiant Electric Cyan & Glacial Jade (`#00e5ff` to `#06b6d4`)
- **Caustic Magnification Flares**: Blinding Incandescent Solar Gold & Topaz Amber (`#ffb703`, `#ff9100`)
- **Focal Singularities & Image Peaks**: Diamond Liquid White (`#ffffff`)
- **Photon Ray Streamlines**: Electric Cyan & Solar Gold Trajectory Ribbons

## Specifications

- **Format**: Seamless looping animation (720 frames @ 60 FPS, 12 seconds)
- **Resolution**: 1920×1080 (HD preview) / 3840×2160 (4K master)
- **Engine**: py5 (Python Processing) + NumPy vectorized 2-body complex lens tensor synthesis + regularized magnification mapping + Blinn-Phong specular relief normal shading + vectorized batch trail rendering (`py5.lines()`, `py5.points()`)

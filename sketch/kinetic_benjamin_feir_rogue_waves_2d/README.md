# kinetic_benjamin_feir_rogue_waves_2d

2D Focusing Nonlinear Schrödinger Equation (NLSE) simulation modeling Benjamin-Feir modulational instability, Peregrine breather cresting, and spontaneous oceanic rogue wave formation.

## Concept
Out of a seemingly innocent, regular sea of sinusoidal swells, tiny multiscale perturbations can trigger catastrophic nonlinear self-focusing. Governed by the 2D Focusing Nonlinear Schrödinger Equation, wave energy spontaneously concentrates into towering, localized rogue wave spires—reaching three to five times the ambient wave height—before shedding shimmering spray into the void and collapsing into concentric dispersive shockwaves.

## Techniques
- **2D Focusing Nonlinear Schrödinger Equation**: Solves $i \partial_t \psi + \frac{1}{2} \nabla^2 \psi + \gamma |\psi|^2 \psi = 0$ via the Split-Step Fourier Method (SSFM) in NumPy, utilizing high-order Strang operator splitting and an 8th-order spectral anti-aliasing filter.
- **Benjamin-Feir Modulational Instability**: Seeds unstable sideband wavevector perturbations on an initial plane carrier wave, allowing spontaneous energy condensation and Peregrine breather emergence.
- **3D Ocean Illumination & Blinn-Phong Specular Shading**: Calculates continuous surface normal vectors directly from spatial envelope gradients $\nabla |\psi|$, rendering directional moonlight diffuse illumination, glistening crest specular highlights, and phase singularity vortex fringes.
- **Dynamic 4K Foam & Spray Kinematics**: Tracks over 1,600 physical spray and foam particles spawned at super-critical rogue wave crests ($|\psi| > 2.8$), dynamically propelled along wave propagation vectors with motion-blurred additive particle trails.

## Palette
- **Deep Oceanic Abyss**: Abyssal Void, Midnight Navy
- **Swell Body**: Rich Cobalt Sapphire, Indigo
- **Wave Crests**: Luminous Electric Cyan, Sea-Glass Teal
- **Rogue Wave Spires & Spray**: Incandescent Sunlit Gold, Blinding Pure White

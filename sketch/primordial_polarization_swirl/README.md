# primordial_polarization_swirl

A visualization of the faint, swirling echoes of the Big Bang's gravitational waves imprinted as B-mode polarization patterns on the Cosmic Microwave Background.

## Concept
The Cosmic Microwave Background (CMB) contains patterns of light polarization. "E-modes" represent gradient patterns, while "B-modes" represent curl or swirl patterns. These B-modes are thought to be caused by primordial gravitational waves from the period of cosmic inflation.

## Visuals
- **Cosmic Sphere**: 120,000 particles initialized on a sphere, expanding slowly to represent the Hubble flow.
- **Swirl Fields**: Particles are advected by a multi-harmonic curl-dominant field, creating complex topological swirls.
- **Color Palette**: 
  - **Ionized Cobalt**: Dominant polarization intensity.
  - **Amethyst / Amber**: Secondary and accent field fluctuations.
- **Aesthetic**: "Quiet/Minimal" with a dark midnight blue background and a high-density background starfield.

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60fps
- **Implementation**: py5 (Processing for Python) + Vectorized NumPy for performance.
- **Duration**: 12 seconds.

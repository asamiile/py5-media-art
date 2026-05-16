# bioluminescent_shear_tide

A 12-second 4K/60fps animation capturing the fleeting glow of microscopic organisms in a midnight tide pool.

## Theme
The fleeting, brilliant glow of microscopic organisms in a midnight tide pool, triggered by the mechanical stress of shifting currents and breaking waves.

## Technique
2D fluid-shear simulation. Tracers are advected by a multi-harmonic velocity field (representing tidal surges). A "bioluminescent" buffer excites based on local shear stress ($|\partial u / \partial y| + |\partial v / \partial x|$), which modulates the alpha and color of 120,000 tracers.

## Palette
- **Background**: Midnight Teal
- **Dominant**: Bioluminescent Emerald
- **Secondary**: Phosphorus Cyan
- **Accent**: Foam White

## Generation
Implemented in py5 with NumPy-vectorized fluid dynamics and additive spectral blending.

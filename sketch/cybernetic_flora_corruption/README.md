# cybernetic_flora_corruption

![Preview](cybernetic_flora_corruption_p1.png)

## Metadata
- **Date**: 2026-05-22
- **Theme**: Organic growth trying to establish order, but constantly being disrupted by vibrant digital corruption.
- **Technique**: Procedurally generated cybernetic floral structures (Maurer-inspired roses) rotating and blooming over time, rendered with RGB channel splitting. A secondary NumPy pixel-manipulation pass introduces horizontal datamoshing and block tears across the canvas. 15s 60fps MP4.
- **Logic Lab Reference**: None

## Concept
A delicate, geometric flower blooms slowly in the obsidian void. As it opens, its structural integrity stutters and shears, bleeding intense neon cyan, magenta, and yellow data across the frame, leaving vibrant datamosh trails in its wake.

## Technical Details
- **Renderer**: P2D / default py5
- **Simulation**: Parametric geometry, random temporal shifts
- **Visuals**: Additive blending, high-frequency glitch noise, RGB channel separation, horizontal block shifting (NumPy).
- **Animation**: 15 seconds at 60fps

# paper_marbling

![Preview](preview_p1.png)

## Metadata
- **Date**: 2026-04-26
- **Theme**: craft, textile, fluid, Turkish ebru, Ottoman art, paper marbling
- **Technique**: ink-drop radial expansion (new_d = sqrt(d²+r²)), alternating x/y sinusoidal comb strokes with decaying amplitude, smooth palette interpolation across 6 jewel-tone colours in 5 stripe cycles, Gaussian grain post-processing

## Concept
Ebru paper marbling simulation: 7–11 ink drops push the colour-stripe field radially outward, then 5–9 alternating comb strokes apply sinusoidal warps to create the characteristic Ottoman marbling pattern; peacock blue, emerald, gold, cream, burgundy, and midnight navy flow in complex organic bands

## Technical Details
- **Renderer**: P2D
- **Simulation**: ink-drop radial expansion (new_d = sqrt(d²+r²))
- **Visuals**: alternating x/y sinusoidal comb strokes with decaying amplitude, smooth palette interpolation across 6 jewel-tone colours in 5 stripe cycles, Gaussian grain post-processing

# prussian_legendre_strata

## Overview
- **Genre**: Mathematical / Abstract Topology
- **Composition Archetype**: Stratified Horizon / Diagonal Sweep
- **Motion Archetype**: Poly-Rhythmic Phase Interference
- **Palette Family**: Rich Saturated Color Field
- **Format**: Animation (`23s (1380 frames @ 60fps)`, 3840×2160 4K)
- **Technique**: `P2D + GLSL + PostFX`

## Concept & Visual Architecture
`prussian_legendre_strata` visualizes a diagonally swept algebraic foliation of Legendre-Chebyshev orthogonal polynomials across a rich saturated color field of deep Prussian blue (`#0a1e40`), forest malachite (`#0e5750`), verdigris turquoise (`#24a89e`), burnt sienna (`#c04424`), and luminous cadmium gold (`#f4ac24`).

In GLSL (`prussian_legendre_strata.glsl`), seven stratified polynomial horizon sheets and higher-order harmonic wave trains (`T2`, `T3`, `T4`, `T5`, `T7`) drift at poly-rhythmic temporal ratios (`1:2:3`), generating luminous algebraic caustics. Layered over the GPU field, 32 calligraphic polynomial ribbons and stationary-inflection tangent rulings trace the evolving envelopes via batched `py5.QUADS` and `py5.LINES`.

## Run
```bash
uv run python sketch/prussian_legendre_strata/main.py
```


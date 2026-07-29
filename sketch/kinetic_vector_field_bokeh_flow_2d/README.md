# kinetic_vector_field_bokeh_flow_2d

**Date**: 2026-07-24
**Type**: Animation (1200 frames, 60fps)

## Concept
A serene, kinetic visualization of a continuous vector field propelling soft, glowing bokeh orbs across the canvas. Driven by 3D Simplex noise (`py5.os_noise`), 300 large particles advect through an undulating force field, overlapping and blending additively to create luminous, ethereal optics akin to out-of-focus city lights or bioluminescent underwater currents.

## Techniques
- **3D Simplex Noise Vector Field**: Force angles are sampled from 3D OpenSimplex noise (`nx = x * 0.002`, `ny = y * 0.002`, `nz = t * 2.0`), producing smooth, non-repeating directional flows that evolve gradually over time.
- **Velocity Integration & Friction**: Particles accelerate along the noise field vector (`force * 0.2`) and experience a damping friction coefficient (`0.92`), resulting in realistic fluid momentum and smooth curvilinear trajectories.
- **Dual-Layer Bokeh Rendering**: Each particle renders as a large, low-alpha outer aura (`fill(hue, 90, 100, 15)`, `size = BRUSH_SIZE * scale`) and a concentrated core (`circle(x, y, size * 0.1)`, `alpha = 200`).
- **Additive Blending & Motion Trails**: Overlapping particles in `py5.ADD` blend mode generate glowing hotspots where multiple auras intersect. A subtle `py5.BLEND` black rectangle (`fill(0, 0, 0, 15)`) drawn at the start of each frame creates delicate, soft-fading trails behind the drifting orbs.
- **Toroidal Boundary Wrapping**: Particles crossing canvas boundaries wrap seamlessly around the screen (`x %= width`, `y %= height`), maintaining constant particle density across the 20-second loop.

## Palette
HSB Color Mode:
- **Background**: Pitch black (`HSB(0, 0, 0)`) with semi-transparent black trail clearing.
- **Orbs**: Shimmering cool hues ranging from **Cyan** through **Blue** to **Magenta** (`Hue 180° - 300°`), continuously shifting over time (`py5.frame_count * 0.2`). Intersecting orbs additively combine into brilliant glowing whites.

# kinetic_optical_illusion_droste_spiral_2d

A mesmerising geometric animation leveraging complex conformal mapping to create a spiraling infinite tunnel (the Droste effect / Escher spiral).

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames, seamless loop)

## Implementation
This sketch constructs a uniform Cartesian grid in a logarithmically transformed space where the coordinates are $(u = \ln(r), v = \theta)$. By applying a linear translation and shear to this grid over time, and then mapping the vertices back to standard Cartesian space via the inverse exponential function $r = e^u$, the grid transforms into an infinite, spiraling tunnel. 
A classic high-contrast checkerboard pattern is applied to the cells. Because the animation shifts the grid by an exact integer multiple of the tile dimensions over the 900 frames, the zoom and rotation form a mathematically perfect, seamless infinite loop that draws the eye endlessly into the center of the canvas.

# kinetic_hyperbolic_reaction_diffusion_2d

Non-Euclidean reaction-diffusion system modeled on a Poincaré disk metric inside a conformally flat 2D canvas.

## Concept
This artwork explores how chemical pattern formation (using the Gray-Scott model) responds to non-Euclidean geometry. By simulating reaction-diffusion on a Poincaré disk with the Laplace-Beltrami operator, diffusion rates freeze gracefully as they approach the hyperbolic horizon ($r \to 1$), creating dense, organic micro-structures that compress toward the outer edge.

## Techniques
- **Poincaré Disk Metric Integration**: Maps non-Euclidean geometry by simplifying the Laplace-Beltrami operator on a conformally flat 2D metric: $\Delta_{LB} f = \Omega^2 \nabla^2 f$.
- **Conformal Factor Scaling**: Precomputes $\Omega^2 = \frac{(1-r^2)^2}{4}$ across a square mesh and multiplies the discrete Euclidean Laplacian stencil directly by this grid factor.
- **Dynamic Glow Rendering**: Maps density ratios of chemical species V into a luminous blending of space void blues, neon magenta, and glowing mint green.
- **4K Overlay**: Draws high-resolution boundary ring overlays to define the Poincaré boundary cleanly.

## Palette
- **Void Base**: Deep Space Blue, Cobalt Violet
- **Reaction Glow**: Luminous Magenta, Electric Mint Green
- **Boundary**: Glowing Turquoise

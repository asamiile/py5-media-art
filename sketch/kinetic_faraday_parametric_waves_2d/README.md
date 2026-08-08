# kinetic_faraday_parametric_waves_2d

A 4K kinetic visualization of Faraday wave instabilities on a vertically vibrated fluid surface, solving the parametrically forced wave equation.

![Preview](kinetic_faraday_parametric_waves_2d_p1.png)

## Concept

When a liquid layer is vertically vibrated, flat surface states undergo parametric resonance (Faraday instability) above a threshold acceleration. This work integrates a 2D Finite-Difference Time-Domain (FDTD) wave solver of the parametrically driven Mathieu wave equation with nonlinear cubic damping:
$$\frac{\partial^2 u}{\partial t^2} + \gamma \frac{\partial u}{\partial t} - \left(c^2 - A \cos(\Omega t)\right) \nabla^2 u + \beta u^3 = 0$$
where $u$ is the fluid height, $\gamma$ is damping, $A\cos(\Omega t)$ models the vertical vibration driving force, and $\beta u^3$ is a cubic saturation term that stabilizes wave amplitude. 

Microscopic fluctuations are constantly injected as seed noise, which rapidly crystallizes into organized, pulsating square and striped grid patterns as the parametric forcing drives the surface unstable.

## Techniques

- **FDTD Parametric Wave PDE Solver**: Vectorized explicit second-order finite difference integration of the forced Mathieu wave equation on a $640 \times 360$ periodic grid using NumPy rolls.
- **Specular Liquid Shading**: Calculates the local surface normal vectors from spatial height gradients, shading the surface using a Specular reflection model to produce a shifting, reflective metallic appearance.
- **4K Upscaling**: Dynamic bilinear expansion from the simulation grid to 3840×2160 pixels inside the py5 framebuffer.
- **Visual Color Blending**: Maps troughs to deep amethyst purple, crests to phosphor cyan, and specular highlights to highly bright liquid platinum.

## Palette

- **Background**: Obsidian Abyss (near black, 8, 6, 12)
- **Dominant**: Liquid Platinum (metallic highlights, 220, 225, 235)
- **Secondary**: Deep Amethyst (troughs and shadows, 100, 30, 220)
- **Accent**: Phosphor Cyan (intense crests, 0, 245, 220)

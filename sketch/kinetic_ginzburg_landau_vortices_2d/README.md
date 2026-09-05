# kinetic_ginzburg_landau_vortices_2d

Time-Dependent Ginzburg-Landau (TDGL) simulation modeling quantized Abrikosov vortex lattice dynamics, dynamic defect pinning, and chiral flux flow in a Type-II superconductor.

## Concept
In Type-II superconductors subjected to an external perpendicular magnetic field, magnetic flux penetrates the material in quantized units known as Abrikosov vortices. This artwork simulates the complex order parameter $\psi(\mathbf{r}, t)$ evolving under the Time-Dependent Ginzburg-Landau equation. Vortices spontaneously nucleate, repel each other into hexagonal Abrikosov lattices, and are captured or sheared by dynamic orbiting pinning defects, creating a mesmerizing dance of topological defects and quantum phase currents.

## Techniques
- **Time-Dependent Ginzburg-Landau (TDGL)**: Integrates $\frac{\partial \psi}{\partial t} = (1 - V_{\text{pin}}) \psi - |\psi|^2 \psi + \mathcal{D}^2 \psi$ using gauge-covariant sub-stepping.
- **Gauge-Covariant Lattice Derivative**: Implements the covariant Laplacian using Peierls phase links under Landau gauge ($\mathbf{A} = (0, Bx, 0)$), ensuring exact gauge invariance and uniform magnetic flux.
- **Dynamic Pinning Centers**: Orbiting Gaussian potential wells ($V_{\text{pin}}$) that model microscopic crystal impurities, dragging, trapping, and releasing vortex bundles.
- **Domain & Core Coloring**: The phase angle $\arg(\psi)$ maps to a deep spectral violet/indigo flow, while zero-amplitude vortex cores ($|\psi| \to 0$) glow with high-intensity cyan, surrounded by warm saffron flux halos.

## Palette
- **Background**: Pitch Black
- **Superconducting Phase**: Deep Amethyst, Cobalt Violet, Indigo
- **Vortex Cores**: Luminous Cyan, Electric Teal
- **Magnetic Halos**: Saffron Gold, Solar Amber

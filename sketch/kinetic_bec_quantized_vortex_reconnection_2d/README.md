# kinetic_bec_quantized_vortex_reconnection_2d

**Type**: Kinetic 2D Macroscopic Quantum Fluid Simulation (15s @ 60 FPS Master Animation)  
**Author**: py5 Media Art Autonomous Agent  
**Date**: 2026-09-27  
**Branch**: `feature/works-20260927`  

---

## 1. Concept & Physical Foundation

A **Bose-Einstein Condensate (BEC)** is a state of matter formed by dilute bosons cooled to temperatures infinitesimally close to absolute zero ($T \to 0$ K). Under these conditions, a macroscopic fraction of atoms occupies the lowest quantum ground state, collapsing individual atomic wavefunctions into a single coherent **macroscopic order parameter**:
$$\Psi(\mathbf{r}, t) = \sqrt{\rho(\mathbf{r}, t)} \, e^{i \theta(\mathbf{r}, t)}$$

The condensate's dynamics are governed by the non-linear **Gross-Pitaevskii Equation (GPE)**:
$$i \hbar \frac{\partial \Psi}{\partial t} = \left( -\frac{\hbar^2}{2m} \nabla^2 + V_{\text{trap}}(\mathbf{r}) + g |\Psi|^2 \right) \Psi$$

In a superfluid BEC, vorticity is strictly topological and quantized. Around any vortex core, the quantum phase $\theta(\mathbf{r})$ must wind by an integer multiple of $2\pi$:
$$\oint \mathbf{v}_s \cdot d\mathbf{l} = \frac{\hbar}{m} \oint \nabla \theta \cdot d\mathbf{l} = \frac{h}{m} n, \quad n \in \mathbb{Z}$$

At the center of each quantized vortex, the superfluid density $\rho(\mathbf{r})$ vanishes identically over the **healing length** $\xi = \hbar / \sqrt{2m g \rho_0}$. When two counter-rotating quantized vortices collide, they undergo **topological vortex reconnection**: the two singularity lines bridge, reconnect, and exchange topological endpoints in a non-adiabatic quantum jump, radiating outward bursts of dispersive Bogoliubov acoustic sound shockwaves.

Simultaneously, planar density depressions known as **dark solitons** (which carry a $\pi$ phase jump) undergo the transverse **snake instability**, developing sinusoidal undulations that buckle and decay into vortex dipole pairs.

---

## 2. Visual & Algorithmic Design

- **Harmonic Trap & Thomas-Fermi Envelope**:  
  Vectorized 2D parabolic trapping potential $V_{\text{trap}}(r)$ confining the macroscopic condensate within the Thomas-Fermi radius $R_{\text{TF}}$.
- **8 Quantized Vortices & Dipole Reconnection**:  
  Vortices orbiting within the trap, colliding as dipoles and reconnecting their phase singularities, with local core density profile $\rho_c = d^2 / (d^2 + 2\xi^2)$ and analytical phase winding $\theta = \sum q_k \arctan2(y - y_k, x - x_k)$.
- **Dark Soliton Snake Instability**:  
  Undulating dark soliton stripe breaking symmetry across the condensate midplane.
- **Bogoliubov Acoustic Phonon Emission**:  
  Concentric dispersive density waves radiating outward from reconnection events.
- **Dual-Light Blinn-Phong Specular Quantum Condensate Optics**:  
  Surface normal mapping over the macroscopic density field $\rho(\mathbf{r})$ and quantum phase interference fringes, producing glistening liquid-crystal highlights on the ultra-cold droplet.
- **2,400 Superfluid Atom Tracers**:  
  Lagrangian tracers circulating with irrotational quantum circulation ($v \propto 1/r$).

---

## 3. Color Palette

- **Ultra-Cold Vacuum Abyss**: Midnight Obsidian (`#010209`)
- **Superfluid Bulk**: Luminous Emerald (`#00ffaa`) & Deep Sapphire Cobalt (`#0033aa`)
- **Vortex Singularities & Solitons**: Neon Laser Fuchsia (`#ff0088`) & Amethyst Violet (`#7700cc`)
- **Acoustic Phonon Shocks**: Incandescent Solar Amber (`#ffaa00`) & Topaz Flame
- **Specular Facets & Highlights**: Pure Diamond White (`#ffffff`)

---

## 4. Technical Specifications

- **Resolution**: 1920 × 1080 (Full HD master)
- **Frame Rate**: 60 fps
- **Total Duration**: 900 frames (15.0 seconds seamless loop)
- **Engine**: py5 (Python Processing 4 bridge) in `P2D` OpenGL mode
- **Compression**: H.264 High Profile 5.1, YUV420p, CRF 18

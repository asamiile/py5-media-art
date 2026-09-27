# kinetic_topological_valley_hall_photonic_crystal_2d

**Type**: Kinetic 2D Topological Photonics Simulation (15s @ 60 FPS Master Animation)  
**Author**: py5 Media Art Autonomous Agent  
**Date**: 2026-09-27  
**Branch**: `feature/works-20260927`  

---

## 1. Concept & Physical Foundation

The **Topological Valley Hall Effect** in photonic crystals enables backscattering-immune light transport along arbitrary paths—including sharp 60° and 120° corners—without requiring external magnetic fields or breaking time-reversal symmetry ($T$).

In a conventional two-dimensional honeycomb or triangular dielectric lattice, the band structure possesses two inequivalent degenerate Dirac cones at the corners of the first Brillouin zone (the $K$ and $K'$ high-symmetry points). By deliberately breaking the spatial inversion symmetry ($P$)—for instance, by perturbing the relative radii or orientations of sublattices $A$ and $B$ ($\Delta r = r_A - r_B \neq 0$)—the Dirac degeneracy is lifted, opening a complete topological photonic bandgap.

Around the $K$ and $K'$ valleys, the energy bands acquire non-zero, localized Berry curvature $\Omega_z(\mathbf{k})$ with opposite signs:
$$\Omega_z(K) = -\Omega_z(K') \neq 0$$

Integrating the Berry curvature over each individual valley yields quantized **Valley Chern Numbers**:
$$C_V = C_K - C_{K'} = \pm 1$$

When two photonic crystal domains with inverted inversion-symmetry-breaking perturbations ($\Delta r > 0$ and $\Delta r < 0$) are placed adjacent to one another, the bulk-boundary correspondence dictates the existence of **topologically protected chiral edge states** along the domain wall interface. These edge states are locked to the valley pseudospin, preventing intervalley scattering ($K \to K'$) from smooth defects and sharp bends.

---

## 2. Visual & Algorithmic Design

- **Honeycomb & Triangular Resonator Array**:  
  Vectorized 2D dielectric pillar potential modeling triangular prisms on a honeycomb lattice. In the upper domain ($y > y_{\text{wall}}$), upward-pointing triangular pillars dominate; in the lower domain ($y < y_{\text{wall}}$), downward-pointing triangular pillars dominate, explicitly revealing the spatial inversion symmetry breaking.

- **Trapezoidal Waveguide Interface with 60° / 120° Bends**:  
  A canonical benchmark topological conduit with two sharp corners (60° turn into an inclined segment, 120° turn into a horizontal plateau). Light traverses these sharp corners with unity transmission ($T \approx 100\%$) and zero backscattering.

- **Topologically Protected Propagating Wavepackets**:  
  Evanescent Bloch wavepackets tightly confined to the domain wall interface ($\Delta \sim 0.42$ lattice constants), with sinusoidal phase fronts propagating along the arc length $s$ with group velocity $v_g$.

- **Dual-Light Blinn-Phong Specular Crystal Chrome Optics**:  
  Surface normal mapping over dielectric pillars and the optical energy density field, producing glistening specular facet glints on the micro-fabricated semiconductor chip.

- **Multi-Species Lagrangian Kinematics**:  
  - **120 Poynting Streamline Ribbons**: Flowing along the domain wall, tracing energy flux trajectories through sharp bends.
  - **2,800 Dirac Quasiparticle Sparks**: Bioluminescent photon wavepackets streaming through the conduit.

---

## 3. Color Palette

- **Substrate Abyss**: Midnight Obsidian (`#02030d`)
- **Top Domain (Valley $K$)**: Electric Glacial Cyan (`#00f5ff`) & Deep Cobalt Azure (`#0033aa`)
- **Bottom Domain (Valley $K'$)**: Radiant Laser Cerise/Magenta (`#ff0077`) & Royal Amethyst Violet (`#6600cc`)
- **Topological Edge Mode & Photons**: Incandescent Solar Gold (`#ffb700`) & Amber Fire (`#ff5500`)
- **Specular Facets & Highlights**: Liquid Diamond Chrome (`#ffffff`)

---

## 4. Technical Specifications

- **Resolution**: 1920 × 1080 (Full HD master)
- **Frame Rate**: 60 fps
- **Total Duration**: 900 frames (15.0 seconds seamless loop)
- **Engine**: py5 (Python Processing 4 bridge) in `P2D` OpenGL mode
- **Compression**: H.264 High Profile 5.1, YUV420p, CRF 18

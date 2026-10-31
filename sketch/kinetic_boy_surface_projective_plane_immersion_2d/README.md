# kinetic_boy_surface_projective_plane_immersion_2d

**Genre**: Mathematical / Abstract Topology / Differential Geometry  
**Format**: 4K UHD (3840×2160), 60 fps, 720 frames (12.0s seamless harmonic loop)  
**Palette**: Warm Ivory Drafting Vellum (`#f8f6f0`), Prussian Blue (`#1a4473`), Venetian Crimson (`#a82a3e`), Amber Meridian (`#d97706`), Antique Gold (`#b48c55`), Muted Slate Graphite (`#46505f`)

---

## Concept & Mathematical Formulation

*Werner Boy Surface Projective Plane Immersion 2D* is an autonomous generative media artwork celebrating differential topology and the immersion of the Real Projective Plane $\mathbb{RP}^2$ into Euclidean 3-space $\mathbb{R}^3$ without singular points or branch cuts.

In 1901, Werner Boy—a doctoral student under David Hilbert in Göttingen—disproved Hilbert's conjecture that non-orientable closed surfaces could not be smoothly immersed in $\mathbb{R}^3$. Boy constructed the first smooth immersion of $\mathbb{RP}^2$, which famously became the emblem of the *Mathematisches Forschungsinstitut Oberwolfach*.

In 1986, Robert Bryant and Rob Kusner discovered an elegant conformal parametrization of Boy's surface minimizing Willmore elastic energy ($W = \int H^2 \, dA = 12\pi$). Using complex stereographic coordinates on the unit disk $z = r e^{i\theta} \in \mathbb{D} \subset \mathbb{C}$ ($|z| < 1$):

$$denom = z^6 + \sqrt{5}z^3 - 1$$

$$f_1 = -\frac{3}{2}\operatorname{Im}\left(\frac{z(1 - z^4)}{denom}\right), \quad f_2 = -\frac{3}{2}\operatorname{Re}\left(\frac{z(1 + z^4)}{denom}\right), \quad f_3 = \operatorname{Im}\left(\frac{1 + z^6}{denom}\right) - \frac{1}{2}$$

$$(X, Y, Z) = \frac{(f_1, f_2, f_3)}{f_1^2 + f_2^2 + f_3^2}$$

### Key Topological Features
1. **Non-Orientability & Möbius Twist**: The surface possesses only one side; moving continuously along coordinate curves reverses normal orientation. Rendered in two-tone non-orientable coloring (Prussian blue `#1a4473` on one winding sheet, Venetian crimson `#a82a3e` on the other).
2. **Three-Fold Rotational Symmetry ($C_3$)**: The surface exhibits exact 3-fold symmetry about its vertical axis, rotating through three seamless lobes in the 12.0s period.
3. **Triple Point Singularity ($\mu = 3$)**: Three self-intersecting sheets pass through each other at the center, intersecting at mutually orthogonal $90^\circ$ tangent angles ($T_1 \perp T_2 \perp T_3$).
4. **Topological Invariants**: Euler characteristic $\chi(\mathbb{RP}^2) = 1$; total Gaussian curvature $\int_M K \, dA = 2\pi$.

---

## Archival Vellum Drafting Aesthetic

The artwork is presented as an archival mathematician's drafting sheet on warm ivory vellum (`#f8f6f0`) with:
- **Depth-Sorted Painter's Shading**: 3,800+ quads sorted by Euclidean camera depth ($Z_{\text{depth}}$) producing realistic physical occlusion across intersecting sheets.
- **Asymptotic & Meridian Filaments**: Amber coordinate rings (`#d97706`) and Prussian blue radial fibers (`#1e3a5f`).
- **Circulating Meron Particles**: 60 harmonic coordinate quanta flowing along the sheets in harmonic phase.
- **Four Corner Differential Geometry Apparatus Cards**:
  - *Top-Left*: Bryant-Kusner Weierstrass-Enneper Conformal Representation on the Riemann Sphere $S^2$.
  - *Top-Right*: Gauss-Bonnet Topological Invariants & Cross-Cap Model ($\chi = 1$).
  - *Bottom-Left*: Triple Point Orthogonal Tangent Triad ($T_1 \perp T_2 \perp T_3$).
  - *Bottom-Right*: Principal Curvature Tensor Spectrum ($K_{\text{max}}, K_{\text{min}}$) with dynamic telemetry meter.
- **Framing & Typography**: Archival double borders with antique gold trim and Latin typography (strictly zero artist signatures/seals).

---

## Execution & Output

```bash
uv run python sketch/kinetic_boy_surface_projective_plane_immersion_2d/main.py
```

- **Preview**: `kinetic_boy_surface_projective_plane_immersion_2d_p1.png`
- **Animation**: `output.mp4` (H.264, 4K 60fps, 720 frames, 12.0s loop)

# kinetic_solutal_marangoni_tears_of_wine_2d

**kinetic_solutal_marangoni_tears_of_wine_2d** is an algorithmic media art animation simulating the non-equilibrium fluid dynamics of the **solutal Marangoni effect**, contact-line finger instabilities, and the famous **Tears of Wine** (*lacrimae vini*) phenomenon.

## Concept & Solutal Marangoni Hydrodynamics

When wine (an ethanol-water solution) sits in a glass, alcohol evaporates faster from the thin climbing meniscus adhering to the vertical glass wall than from the bulk reservoir below. Because ethanol lowers the surface tension of water, the liquid higher up the wall becomes depleted of alcohol and develops a higher surface tension than the bulk liquid:
$$\frac{\partial c}{\partial Y} < 0 \implies \tau_{\text{Marangoni}} = \frac{\partial \gamma}{\partial Y} = \frac{\partial \gamma}{\partial c} \frac{\partial c}{\partial Y} > 0$$

1. **Upward Solutal Marangoni Pumping**:
   This vertical surface tension gradient generates an upward Marangoni shear stress $\tau_{\text{Marangoni}}$ that drives a thin liquid sheet climbing *upward* along the glass wall against gravity:
   $$j_{\text{film}} = \frac{\tau h^2}{2\mu} - \frac{\rho g h^3}{3\mu}$$

2. **Rim Accumulation & Contact-Line Finger Instability**:
   As the climbing film ascends, fluid accumulates in a horizontal rim ridge around $Y \sim 2.45$. When the accumulated volume exceeds gravitational and capillary stability, a transverse contact-line instability spontaneously breaks the translational symmetry into periodic rivulets and cusped fingers with dominant wavenumber $k_x$:
   $$Y_{\text{rim}}(X, t) = Y_0 + \sum_m A_m \sin(m k_x X + \phi_m(t))$$

3. **Weeping Pendant Tears of Wine**:
   At the finger tips, fluid pools into heavy pendant droplets ("tears"). Once a droplet's mass exceeds capillary retention, it slides downwards under gravity in a glistening tear rivulet, rejoining the bulk meniscus below and sustaining a continuous, rhythmic hydrodynamic cycle.

4. **3D Surface Profile & Specular Caustic Refraction**:
   Dynamic 3D surface height profile $H(X, Y)$ is evaluated with surface normal vectors $\vec{n} = (-\nabla H, 1) / \|\dots\|$, illuminated by dual light sources (warm candle gold ambient and cool crystalline rim highlights) to capture realistic liquid mirror reflections and glass caustics.

## Visual Composition (60-30-10 Palette)

- **60% Wine-Cellar Obsidian Void & Deep Cabernet Violet**: Cellar ambient darkness (`#040108`), glass reflections, and deep cabernet violet shadows (`#0c0312`, `#180620`).
- **30% Solutal Fluid Ribbon Burgundy, Ruby & Glacial Azure Meniscus**: Climbing fluid film and cascading rivulets (`#991b1b`, `#e11d48`), with alcohol refraction tint (`#0284c7`, `#38bdf8`).
- **10% Incandescent Meniscus White-Gold & Alcohol Vapor Wisps**: Brilliant rim caustic crest and glistening pendant tear beads (`#ffffff`, `#fef08a`, `#fbbf24`), with evaporating vapor wisps (`#e879f9`).

## Execution

```bash
uv run python sketch/kinetic_solutal_marangoni_tears_of_wine_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_solutal_marangoni_tears_of_wine_2d.mp4`)
- Preview snapshot: `kinetic_solutal_marangoni_tears_of_wine_2d_p1.png`

# kinetic_brutalist_tectonic_cantilever_shadows_2d

Kinetic axonometric brutalist megastructure and dynamic solar shadow study executed in py5.

## Concept

An architectural homage to heroic mid-century Brutalism (*béton brut*), Brazilian Paulista school massing, and monumental tectonic geometry. A heroic complex of massive board-formed concrete slabs, sliding cantilever balconies, vertical brise-soleil sun louvers, and stepped plazas rests upon a vast podium.

Set within the complex is a sunken Aegean cerulean reflecting pool whose surface ripples with delicate wave caustics. A dynamic solar vector completes a full 360-degree orbital rotation, casting dramatic, crisp geometric shadows across the podium deck and warm travertine drafting paper vellum, turning the entire architectural composition into a living kinetic sundial.

## Technical Details

- **Resolution**: 3840×2160 (4K UHD)
- **Duration**: 720 frames @ 60 FPS (12.0s seamless $C^1$ loop)
- **Genre Taxonomy**: Architectural / Brutalism / Geometric
- **Axonometric Projection**:
  - 30-degree isometric projection: $u = c_x + (x - y) \cos(30^\circ)$, $v = c_y + (x + y) \sin(30^\circ) - z$.
  - Depth-sorted painter's occlusion order for accurate geometric overlaps.
- **Solar Lighting & Multi-Tier Shadow Casting**:
  - Orbiting solar vector: $\vec{s}(t) = (\cos(\omega t), \sin(\omega t), -\tan(48^\circ))$.
  - Dual-tier projection: contact shadows cast onto both the ground datum ($z=0$) and elevated podium deck ($z=35$).
- **Kinematic Cantilevers**:
  - Independent harmonic sliding displacements along $X$ and $Y$ axes: $dx_1(t) = 125 \sin(\omega t)$, $dy_1(t) = 95 \cos(\omega t)$, $dx_2(t) = -85 \sin(\omega t)$.
  - Guaranteed seamless loop: values and velocity vectors at $t=0$ and $t=T$ match exactly.
- **Architectural Detailing & Materiality**:
  - Ground: Warm Travertine drafting vellum (`#ece8de`) with faint construction grid lines.
  - Concrete Slabs: Board-formed timber shuttering lines, tie-rod anchor holes, and multi-tone directional daylight illumination.
  - Water: Aegean Cerulean reflecting pool (`#1280b9`) with animated wave interference caustics.
  - Accent: Bauhaus / Brutalist safety vermilion (`#dc2626`) edge bands and technical datum lines.
  - Drafting Dial: Working solar azimuth compass dial in the bottom right corner showing the sun's orbital angle.
- **Anonymity**: 100% autonomous algorithmic generative art without human authorship marks, signatures, or name seals.

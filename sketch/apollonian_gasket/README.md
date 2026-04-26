# apollonian_gasket

**Theme**: "Recursive tangency" — Apollonian gasket from the (−1,2,2,3) starting quadruple; every gap between three mutually tangent circles is filled by the unique inscribed circle computed via Descartes' theorem; the fractal boundary shrinks to a dust of infinite depth.

**Technique**: No-sqrt inverse Descartes formula (`k_new = 2(k₁+k₂+k₃) − k_old`, `z_new = (2(k₁z₁+k₂z₂+k₃z₃) − k_old·z_old) / k_new`); iterative BFS from 4-circle seed; 6-stop curvature-octave palette (gold→coral→magenta→violet→cerulean→teal) encodes circle size as color.

**Description**: Starting from four mutually tangent circles with curvatures (−1, 2, 2, 3), the BFS recursively fills every gap until circles reach radius 0.004 of the unit disk. Each circle is colored by its curvature octave (log₂(k)) cycling through a 6-stop warm-to-cool palette; opacity and brightness fade for the smallest circles, revealing the fractal dust at the limit set boundary.

**Palette**:
- Background: `#05080f` near-black
- Curvature octaves: warm gold · coral · magenta · deep violet · cerulean · teal

**Preview**: `preview.png`

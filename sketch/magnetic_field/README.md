# magnetic_field

**Theme**: "Invisible geometry" — the magnetic dipole field made visible; the hidden order that governs compass needles and aurora formations

**Technique**: Euler streamline integration of the analytic dipole field B(r) = Σ charge·(r−r_pole)/|r−r_pole|³, seeded at uniform angles from the N pole

**Description**: 72 field lines are seeded at evenly-spaced angles around the north pole and integrated using the summed contribution of both poles (N positive, S negative). Lines that successfully connect N→S are rendered with a smooth warm-red→cold-blue gradient encoding the direction of flow. Escaping lines appear as dim peripheral arcs. The two poles are marked with colored halos at the convergence points.

**Palette**:
- Background: `#0c0a0e` near-black with warm undertone
- N pole / field origin: `#c85032` warm iron-red
- S pole / field sink: `#325ac8` cold blue
- Gradient: warm red → neutral gray → cold blue along each line

**Preview**: `preview.png`

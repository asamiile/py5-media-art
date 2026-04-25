# particle_life

**Theme**: "Emergent society" — five particle types governed by a random attraction/repulsion matrix; simple pairwise forces produce self-organizing clusters, cell-like membranes, and predator-prey orbits reminiscent of living microorganisms

**Technique**: Full pairwise force computation (N×N vectorized numpy); quadratic force profile in ring [R_MIN, R_MAX] with universal short-range repulsion; toroidal boundary; 250 Euler integration steps with velocity damping (friction=0.82); final state rendered as filled circles per type

**Description**: 1000 particles (200 per type: crimson, gold, teal, violet, sage) start randomly placed. A randomly drawn 5×5 force matrix assigns each type pair a signed attraction/repulsion strength. After 250 simulation steps the system settles: some types form tight clusters with nuclei of other types (resembling cells), others scatter as lone wanderers. Every run produces a unique ecology governed by the same simple rules.

**Palette**:
- Background: `#06050a` near-black
- Crimson: `(210, 55, 65)`
- Gold: `(225, 182, 52)`
- Teal: `(52, 185, 185)`
- Violet: `(155, 55, 222)`
- Sage: `(122, 205, 108)`

**Preview**: `preview.png`

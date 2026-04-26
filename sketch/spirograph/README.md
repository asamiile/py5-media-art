# spirograph

**Theme**: "Machine botany" — eight hypotrochoid rose curves overlaid at the canvas center, each drawn by a different gear ratio, evoking the layered petals of mechanical spirograph drawing instruments

**Technique**: Parametric hypotrochoid equations (x = (R−r)cos t + d·cos((R−r)t/r), y = (R−r)sin t − d·sin((R−r)t/r)) with d = R−r (classic rose mode); each curve closes after r/gcd(R,r) full inner-gear revolutions; normalized to canvas radius; semi-transparent strokes let color overlaps show through

**Description**: Eight rose-curve hypotrochoids with petal counts 4, 5, 6, 7, 8, 9, 11, and 12 are drawn concentrically in distinct colors (crimson, gold, teal, violet, coral, sage green, steel blue, rose). All curves use d = R−r which produces the classic sharp-cusped petal shape without inner loops. The overlapping petals build up a stained-glass mandala where different petal densities create interference patterns at the center and outer ring.

**Palette**:
- Background: `#06060e` near-black deep navy
- 8 curve colors: crimson, gold, teal, violet, coral, sage, steel blue, rose

**Preview**: `preview.png`

# kaleidoscope

**Theme**: "Stained glass mandala" — a 12-fold kaleidoscope; a single 15° wedge of a multi-frequency sine pattern is reflected and rotated to fill a circle, producing a jewel-toned stained-glass window from pure mathematical symmetry

**Technique**: Polar coordinate mapping; each pixel's angle is folded into the canonical sector [0°, 15°] via modulo + reflection; a 3-frequency sine/cosine product pattern is sampled at the canonical (r, θ) coordinates; the result is mapped through a cyclic 4-stop jewel-tone palette

**Description**: Every pixel is assigned to one of the 24 canonical wedge instances through angle folding, giving the 12-fold rotational + reflective symmetry of a physical kaleidoscope. The pattern within the wedge uses three interfering sine harmonics whose product creates organic blob shapes. The cyclic palette — warm gold → cool teal → crimson → deep violet → back to gold — produces layered stained-glass rings radiating from the center. The near-black circle boundary separates the mandala from the dark background.

**Palette**:
- Background: `#06050a` near-black
- Warm gold: `#cd9b1c`
- Cool teal: `#1c989e`
- Crimson: `#9e1c26`
- Deep violet: `#6c1ca8`

**Preview**: `preview.png`

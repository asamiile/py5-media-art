# moire_pattern

**Theme**: "Ghost geometry" — two families of concentric rings from slightly offset centers; their geometric intersections trace moiré ovals and columns that exist nowhere in either ring family alone — pure optical interference from layered regularity

**Technique**: Two distance fields from offset centers (280px apart on the horizontal axis); each distance field modulo ring spacing produces a boolean ring mask; the intersection of both masks (where rings from both families coincide) is rendered in bright lavender-white, the individual families in dark crimson and dark navy

**Description**: Ring family A radiates from the left of center (crimson); ring family B radiates from the right (navy). The two families of 20px-spaced concentric rings interfere at their crossing points, creating bright lavender-white dots that trace elliptic and hyperbolic moiré curves — a classic two-center interference pattern. The spacing between the moiré fringes is entirely determined by the center offset and ring spacing, not by any individual ring's shape.

**Palette**:
- Background: `#07050d` near-black violet
- Ring family A: `#911c1c` dark crimson
- Ring family B: `#1c1c91` dark navy
- Overlap (moiré): `#f2e4ff` bright lavender-white

**Preview**: `preview.png`

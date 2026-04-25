# mandelbrot_set

**Theme**: "Boundary of infinity" — the Mandelbrot set; the parameter space of the quadratic map z → z² + c, where the boundary between bounded and unbounded orbits traces a fractal coastline of infinite complexity

**Technique**: Vectorized numpy escape-time iteration (280 max iterations); smooth coloring via ν = i + 1 − log₂(log₂|z|) eliminates banding at the boundary; 3-stop color gradient maps normalized escape time from far (deep violet) through near-boundary (amber) to the fractal edge (pale gold)

**Description**: Each pixel represents a complex parameter c. The smooth coloring value encodes how quickly the orbit z → z² + c diverges: far-escaping points (left exterior) appear in cold deep violet; as c approaches the fractal boundary, the glow warms through burnt amber to pale gold, illuminating the infinite detail of the set's coastline. The interior (bounded orbits) remains near-black. The classic two-bulb body, its antenna extending left, and the satellite mini-brots along the top are all clearly resolved.

**Palette**:
- Interior (bounded): `#04030e` near-black purple
- Far escape: `#0c0826` deep violet
- Medium iter: `#a8601c` burnt amber
- Near boundary: `#f5e8bc` pale gold

**Preview**: `preview.png`

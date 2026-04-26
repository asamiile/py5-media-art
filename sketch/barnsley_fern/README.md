# barnsley_fern

**Theme**: "Deep frond" — Barnsley's IFS fern; the biological structure of a fern frond emerging from four simple affine transformations applied stochastically

**Technique**: Four affine IFS transforms (stem, main frond self-similarity, left sub-frond, right sub-frond) iterated 800k times; density accumulated into a 2D field; log-scale mapping and a 3-stop color gradient reveal structural layers from dense midrib to delicate leaflet tips

**Description**: 800,000 random IFS iterations trace the Barnsley fern attractor. The dominant transform (prob 0.85) produces the self-similar main frond; two sub-frond transforms (prob 0.07 each) generate the paired lateral leaflets; the stem transform (prob 0.01) produces the thin central axis. Density accumulation with log1p scaling gives the frond its characteristic gradient from dark canopy shadow to bright lit tips. The result is indistinguishable from a photograph of a real fern frond.

**Palette**:
- Background: `#060a05` near-black moss
- Low density: `#0e2a12` dark forest shadow
- Mid density: `#379448` rich fern green
- High density: `#d7eeaf` pale translucent tip

**Preview**: `preview.png`

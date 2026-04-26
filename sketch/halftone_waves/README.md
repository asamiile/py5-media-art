# halftone_waves

**Theme**: "Printed interference" — wave superposition rendered as halftone dots, evoking offset-print lithography and newspaper halftone printing

**Technique**: Two interleaved dot grids offset by half a cell (PITCH/2); Grid A encodes wave-field amplitude as navy dot radius; Grid B encodes the complementary (inverted) amplitude as sienna dot radius; power stretch (field^1.8) sharpens the size contrast between dense and empty zones

**Description**: Four wave point sources placed randomly within the canvas; each source emits cosine waves that interfere. The summed interference amplitude drives dot radius on a regular 22px grid. Large navy dots cluster at constructive interference peaks; large sienna dots fill the complementary troughs. The interleaved two-color grid creates a muted tertiary where both colors are large, and bare cream paper shows where both are small. Every run produces a unique wave topology.

**Palette**:
- Background: `#f8f4ea` warm cream paper
- Grid A: `#182648` deep navy
- Grid B: `#a25828` burnt sienna

**Preview**: `preview.png`

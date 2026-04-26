# hilbert_curve

**Theme**: "Ordered chaos" — the Hilbert space-filling curve at order 8 (256×256 = 65536 cells); a cyclic palette reveals the self-similar U-winding structure across all scales simultaneously, showing how a single thread visits every point without crossing itself

**Technique**: Vectorised d→(x,y) Hilbert mapping via bit-pair extraction and rotation; 65536 cells placed into a 256×256 grid and scaled to canvas; a 3-stop indigo→teal→amber palette cycles 20 times along the curve's 1D path, making the winding path visible as alternating colour bands

**Description**: Each of the 65536 cells in a 256×256 grid is assigned a colour by its position along the Hilbert curve (a 1D index 0–65535). The palette cycles 20 times over this index range, so cells that are nearby on the curve (but far apart in space) share similar colours. The resulting image reveals the self-similar nested U-shape structure at every scale from the full grid down to 4-cell sub-curves — the locality property of Hilbert curves made visible as a colour texture.

**Palette**:
- Background: `#08060e` near-black
- Cycle A: `#160e48` deep indigo
- Cycle B: `#0e9e98` cyan-teal
- Cycle C: `#deae20` warm amber

**Preview**: `preview.png`

# woven_fabric

**Theme**: "Mathematical loom" — a Jacquard-style woven textile where a sinusoidal function acts as the weave matrix; at each warp × weft thread intersection, a sine-cosine product determines which thread lies on top, producing large-scale flowing organic patterns at cloth texture scale

**Technique**: Per-pixel thread classification (warp-only, weft-only, intersection, gap) via modular arithmetic; weave matrix sin(i·0.42)·cos(j·0.35) + 0.55·sin(i·0.17+j·0.28) controls which thread shows at intersections; dark edge shading (60% darkening, 1px) gives threads 3-D rounded appearance

**Description**: 160 vertical warp threads (warm sienna) and 90 horizontal weft threads (cool indigo) cover the canvas at 12px pitch. At each of the ~14,400 intersections, the sinusoidal weave function determines which thread floats on top. Large-scale sinusoidal waves produce organic blob patterns — regions where warp dominates alternate with regions where weft dominates — while the underlying 10px thread texture remains visible throughout, exactly like real Jacquard cloth seen up close.

**Palette**:
- Gaps/background: `#0a080e` near-black
- Warp threads: `#bc5a28` warm sienna
- Weft threads: `#2d4499` cool indigo
- Thread edges: darkened 40% for 3-D relief

**Preview**: `preview.png`

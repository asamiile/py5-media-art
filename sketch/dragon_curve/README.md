# dragon_curve

**Theme**: "Folded infinity" — the Harter-Heighway dragon curve; 15 iterations of folding a paper strip in half produces 32,768 right-angle segments that never cross, yet tile the plane — a fractal from pure repetition.

**Technique**: Binary fold sequence (`turns = [turns, [1], (-turns)[::-1]]`), cumulative angle integration mod 4, 16 color groups cycling through a 4-stop palette to reveal the winding path structure.

**Description**: N_ITER=15 unfolds to 32,767 unit-length segments traced as a single connected path; the path is split into 16 sequential bands, each colored by a cyclic 4-stop palette (deep indigo → coral → teal → warm gold) so the self-similar winding is visible at every scale. The curve never self-intersects yet fills a fractal region of the plane — order from repetition alone.

**Palette**:
- Background: `#06050a` near-black
- Cyclic stops: `#1e1264` deep indigo · `#d24b37` coral · `#1c968c` teal · `#d7a81c` warm gold

**Preview**: `preview.png`

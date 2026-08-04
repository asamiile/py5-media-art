# kinetic_abelian_sandpile_mandala_2d

A 4K kinetic visualization of the **Bak-Tang-Wiesenfeld (BTW) Abelian Sandpile model** — a landmark system in self-organized criticality (SOC). Sand grains are continuously deposited at the center of a 1201×1201 grid. When any cell accumulates 4 or more grains, it topples, distributing one grain to each of its 4 cardinal neighbors. Through millions of cascading toppling events, a breathtaking **fractal mandala** with exact 4-fold rotational symmetry crystallizes from pure local rules.

## Concept

The Abelian Sandpile is one of the most elegant examples of **emergence** in mathematics — impossibly complex global structure arising from a trivially simple local rule. The system spontaneously organizes itself to a critical state where avalanches of all sizes occur, with no characteristic scale. The resulting mandala is:

- Exactly **4-fold rotationally symmetric** (consequence of grid symmetry + abelian property)
- A **fractal** with self-similar structure at all scales
- **Deterministic** — the same sequence of additions always produces the same pattern
- **Infinite in complexity** — as more grains are added, new fine structure perpetually emerges

## Techniques

- **BTW Abelian Sandpile**: Integer grid toppling rule (`≥4 → distribute to 4 neighbors`)
- **NumPy vectorized toppling**: Full-grid boolean mask relaxation, 50 passes/frame
- **Grain ramp**: 2,000→8,000 grains/frame increasing over 20s for accelerating drama
- **4-color grain mapping**: 0=void, 1=violet, 2=teal, 3=gold (mapped via `np.clip` + `COLOR_MAP`)
- **Dynamic zoom**: Active region auto-cropped and upscaled to fill 4K each frame
- **Glow ring**: Pulsing frontier ring at the sandpile's outer edge
- **ARGB pixel blit**: Direct `pimg.pixels[:] = canvas.flatten()` for maximum performance

## Parameters

| Parameter | Value |
|---|---|
| Grid size | 1201 × 1201 |
| Grains per frame | 2,000 → 8,000 (ramped) |
| Topple passes/frame | 50 |
| Total grains (20s) | ~3 million |
| Animation | 20s @ 60fps (1200 frames) |
| Output | 4K (3840 × 2160) |

## Color Mapping

| Grain count | Color | HSB |
|---|---|---|
| 0 | Deep Void | H=240, S=200, V=18 |
| 1 | Electric Violet | H=270, S=240, V=200 |
| 2 | Bioluminescent Teal | H=185, S=255, V=230 |
| 3 | Solar Gold | H=45, S=240, V=255 |

## Mathematical Background

The BTW sandpile was introduced by Per Bak, Chao Tang, and Kurt Wiesenfeld in 1987. The system is "abelian" because the final relaxed state is independent of the order in which topplings are performed — a deep algebraic property that guarantees the fractal mandala's exact symmetry. The group of legal sandpile configurations forms a finite abelian group under addition.

## Output

- `kinetic_abelian_sandpile_mandala_2d.mp4` — 4K 60fps 20-second animation
- `kinetic_abelian_sandpile_mandala_2d_p1.png` — Mid-animation preview frame

# monsoon_resonance

A still pond at midnight under summer monsoon. Each raindrop blooms into expanding rings of light that weave into hypnotic interference shimmer across the dark water.

## Concept

The wave equation in 2D produces something rare in this collection: a process whose visual texture is dictated by *interference* rather than *advection*. Where most particle works draw motion, this work draws coherence — the way independent ring sources, each a single raindrop, layer up into a shifting moiré that has no single author. The pond is mostly black; only the moonlit crests reveal anything is happening at all.

## Technique

- 2D scalar wave equation propagated on a 480×270 grid using a 5-point stencil FDTD scheme: `u_next = (2u − u_prev + c²·∇²u) · damping`.
- Each raindrop deposits a Mexican-hat (Laplacian-of-Gaussian) impulse, seeding multiple concentric bands rather than a single front.
- Two physics sub-steps per rendered frame for smoother propagation.
- Drop frequency follows a `sin¹·⁴` curve: sparse at the start, dense in the middle, easing toward the end.
- Soft border absorber (gradient mask near edges) suppresses boxy reflections at the grid boundary.
- Rendering uses signed surface height: positive deflection blends toward cyan and (for sharp peaks) pearl; negative deflection darkens toward indigo. A faint slope-based rim glint sharpens wave fronts.
- Vectorized NumPy throughout; final color array is nearest-neighbor upscaled and pushed via `py5.np_pixels` (ARGB).

## Palette

- Background: deep midnight indigo (`#040612`)
- Crest: silver-cyan moonlight (`#6EAAD2`)
- Peak highlight: pearl white (`#DCE6F0`)
- Distant lamplight: warm amber (`#DCA55A`)
- Mood: quiet, meditative, monsoon serenity

## Output

- `output.mp4` — 18s @ 60fps, 4K
- `monsoon_resonance_p1.png` — preview from a frame near peak interference

## Run

```bash
uv run python sketch/monsoon_resonance/main.py
```

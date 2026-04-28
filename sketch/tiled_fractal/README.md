# Tiled Fractal

A recursive square subdivision pattern with organic asymmetry and rotation, creating dynamic fractal tiling.

## Technique

Recursive square subdivision with asymmetric quadrant sizes, rotation at each recursion level, and dramatic color gradient transitions. The algorithm breaks perfect grid symmetry through randomized size variations and rotational offsets.

## Color Palette

- Background: Deep charcoal (#1a1a1a)
- Gradient 1: Deep emerald (#106450) → bright teal (#00c8c8)
- Gradient 2: Deep amber (#b46414) → bright coral (#ff7850)
- Accents: Gold (#ffd700) at depth 2, violet (#b464ff) at depth 4
- Mood: Dynamic, organic, geometric

## Visual Impression

A dynamic fractal pattern that breaks mechanical grid symmetry through organic asymmetry and rotation. The squares rotate and subdivide asymmetrically, creating visual movement and energy with dramatic color transitions from deep emerald to bright teal and deep amber to bright coral.

## Parameters

- MAX_DEPTH = 6 (recursion depth)
- MIN_SIZE = 4 (minimum square size)
- Rotation: 22.5° increments at each recursion level
- Asymmetric subdivision: different sizes and offsets for each quadrant
- Seed-based organic variation for reproducible randomness

## Running

```bash
uv run python sketch/tiled_fractal/main.py
```

## Output

- `preview.png` — 1920×1080 preview image
- Change `SIZE` constant in `main.py` for 3840×2160 output

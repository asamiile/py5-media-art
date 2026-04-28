# Ikeda Attractor

A chaotic system that spirals through phase space, revealing hidden order in apparent randomness.

## Technique

Ikeda map — a discrete-time dynamical system that generates complex, spiraling trajectories through phase space, creating organic, flowing patterns that emerge from simple mathematical rules.

## Color Palette

- Background: Deep midnight blue (#0a0e27)
- Dominant (60%): Electric cyan (#00d4ff) with varying intensity
- Secondary (30%): Warm magenta (#ff00aa) for contrast
- Accent (10%): Bright white (#ffffff) for highlights
- Mood: Dark/moody

## Visual Impression

A mesmerizing, glowing spiral that seems to pulse and breathe, with trails that suggest motion through an invisible space.

## Parameters

- U = 0.9 (Ikeda parameter controlling chaos)
- 50,000 iterations for the attractor
- Point-based rendering with alpha blending

## Running

```bash
uv run python sketch/ikeda_attractor/main.py
```

## Output

- `preview.png` — 1920×1080 preview image
- Change `SIZE` constant in `main.py` for 3840×2160 output

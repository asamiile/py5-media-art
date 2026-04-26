# magnetic_pendulum

**Basin of Attraction: Where Chaos Decides Your Fate**

## Concept

Three invisible attractors pulling a swinging pendulum into unpredictable trajectories — the boundary between order and chaos mapped in color. Each pixel represents a starting position, and its color reveals which magnet will ultimately capture the pendulum. The fractal boundaries between basins show where infinitesimal changes in initial conditions lead to completely different outcomes.

## Technique

- Damped magnetic pendulum simulation over 3 equilateral-triangle magnets
- Per-pixel parallel ODE integration (velocity Verlet, up to 800 steps)
- Gravitational restoring force + 1/r² magnetic attraction + linear damping
- Basin identity from convergence target; brightness from convergence speed
- Laplacian edge enhancement at basin boundaries
- Vectorized numpy simulation for ~2M simultaneous trajectories

## Palette

| Role | Color | Description |
|------|-------|-------------|
| Basin A | `#4A2D7A` → `#9966D9` | Deep amethyst to bright purple |
| Basin B | `#1A6B6B` → `#40CCC0` | Muted teal to bright cyan |
| Basin C | `#C47D3E` → `#FFBF66` | Burnished copper to bright gold |

## Parameters

- **Magnets**: 3 at equilateral triangle vertices (random rotation per run)
- **Physics**: gravity=0.2, magnetic=1.0, damping=0.18, height²=0.15
- **Resolution**: 1920×1080 (preview) / 3840×2160 (output)

## How to Run

```bash
uv run python sketch/magnetic_pendulum/main.py
```

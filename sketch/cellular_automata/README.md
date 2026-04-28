# Cellular Automata

Organic emergence from probabilistic computation, where simple rules create complex living patterns.

## Technique

Probabilistic cellular automaton with density-based coloring and age-based color transitions. Unlike deterministic Conway's Game of Life, this system uses probabilistic survival and birth rules that create more organic, natural-looking patterns. Multiple seed clusters evolve through generations, with cells aging over time and density-based golden highlights creating focal points.

## Color Palette

- Background: Deep midnight (#080f19)
- Dominant (60%): Electric magenta (#ff0080) for young cells
- Secondary (30%): Bright teal (#00c8b4) for mature cells
- Accent (10%): Rich gold (#ffd700) for high-density clusters
- Depth: Deep purple (#b400ff) for very old cells
- Mood: Electric/organic

## Visual Impression

A mesmerizing display of organic cellular patterns that evolve and grow like living tissue. Electric magenta young cells transition to bright teal mature cells, with very old cells showing deep purple depth. Golden highlights mark high-density clusters where cells congregate, creating beautiful focal points against a deep midnight background. The probabilistic rules create natural, organic patterns that feel more like biological growth than mechanical computation.

## Parameters

- GRID_SIZE = 200 (simulation grid resolution)
- NUM_GENERATIONS = 180 (number of generations to simulate)
- NUM_SEEDS = 12 (number of random seed clusters)
- SEED_RADIUS = 10 (radius of seed clusters)
- DENSITY_THRESHOLD = 0.5 (density threshold for golden amber highlights)
- Probabilistic survival: 0.3 + 0.7 × (neighbors / 8.0)
- Probabilistic birth: 0.1 × (neighbors / 8.0)

## Running

```bash
uv run python sketch/cellular_automata/main.py
```

## Output

- `preview.png` — 1920×1080 preview image
- Change `SIZE` constant in `main.py` for 3840×2160 output

# Bioluminescent Forest

A mystical forest scene where glowing trees and floating fireflies create an enchanting nighttime atmosphere.

## Technique

Recursive tree structures with randomized parameters (height, branch angles, recursion depth) combined with a particle system featuring swarm behavior. The scene includes depth-based scaling and opacity for 3D spatial relationships, attraction points for organic clustering, varied glow strength based on tree age, ground vegetation with smaller recursive structures, and purple/magenta accents in deeper forest areas.

## Color Palette

- Background: Deep forest dark (#080c14)
- Dominant (60%): Electric teal (#00ffcc) with varying intensity
- Secondary (30%): Warm amber (#ffcc00) for contrast
- Accent (10%): Soft violet (#aa88ff) and deep purple (#b464ff)
- Mood: Dark/moody, mystical

## Visual Impression

A mesmerizing bioluminescent forest where glowing trees and floating fireflies create an enchanting nighttime atmosphere. The scene features organic tree structures with randomized parameters, depth-based layering for 3D spatial relationships, and vibrant color transitions from teal to amber to violet with purple and magenta accents in deeper areas.

## Parameters

- 15 trees with randomized height, branch angles, and recursion depth
- 2000 particles with swarm behavior (cohesion, alignment, wandering)
- MAX_TREE_DEPTH = 6 (recursion depth for trees)
- MIN_BRANCH_SIZE = 3 (minimum branch size)
- Attraction points around tree canopies and forest floor for organic clustering
- Depth-based scaling and opacity for stronger 3D spatial relationships
- Glow strength varies based on tree age, size, and position
- Ground vegetation with smaller recursive structures
- Purple/magenta accents in deeper forest areas

## Running

```bash
uv run python sketch/bioluminescent_forest/main.py
```

## Output

- `preview.png` — 1920×1080 preview image
- Change `SIZE` constant in `main.py` for 3840×2160 output

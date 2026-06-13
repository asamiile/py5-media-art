# fluvial_meander_oxbow_migration_2d

A lowland river slowly rewrites its own path across a floodplain. Bends grow by
curvature-driven lateral migration, necks pinch off into still oxbow lakes, and
the swept floodplain fossilizes the river's history as ochre point-bar scroll
ridges — an aerial geomorphology study of water reshaping land over centuries.

## Concept

- **Theme**: The quiet, geologic patience of a meandering river editing the land.
- **Technique**: A simplified Howard & Knutson meander model. A numpy centerline
  migrates outward along its normal at a rate set by upstream-weighted local
  curvature, so bends amplify and sharpen. The line is arc-length resampled each
  step, and `scipy.spatial.cKDTree` detects neck cutoffs — when two distant parts
  of the channel touch, the enclosed loop is abandoned as a permanent oxbow lake
  and the river takes the shortcut.
- **Floodplain memory**: A persistent `py5` graphics buffer accumulates every
  past channel position as low-alpha sediment plus a thin inner-bank accretion
  ridge, building the concentric scroll-bar texture left by real point bars.

## Palette

Warm/organic with a cool water accent:

- Background: deep warm loam (textured floodplain terrain)
- Scroll deposits: ochre → sienna
- Fresh point-bar ridges: pale sand
- Active channel: cool slate-teal with a bright thalweg core
- Oxbow lakes: desaturated still teal

## Output

- **Format**: Animation, ~20s @ 60fps, 3840×2160
- `output.mp4` — rendered animation (git-ignored)
- `fluvial_meander_oxbow_migration_2d_p1.png` — preview snapshot

## Run

```bash
uv run python sketch/fluvial_meander_oxbow_migration_2d/main.py
```

Each run varies (no fixed seed): the initial bends, migration history, and the
location and number of oxbow cutoffs differ every time.

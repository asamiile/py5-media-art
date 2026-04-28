# Chromatic Aberration

Optical dispersion revealing the hidden rainbow spectrum hidden in white light.

## Technique

Chromatic aberration simulation using wavelength-dependent refraction indices. Creates prismatic color separation through simulated optical elements (convex lenses, prisms, concave lenses) with varying focal lengths and dispersion coefficients. The simulation traces 15000 rays through 8 white light sources, with each ray split into RGB components that bend at different angles based on wavelength, creating organic rainbow patterns across a dark background.

## Color Palette

- Background: Deep charcoal (#1a1a1) with subtle gradient
- Dominant (60%): Spectral rainbow gradient (red→orange→yellow→green→blue→indigo→violet)
- Secondary (30%): White light source (#ffffff)
- Accent (10%): Dark void (#000000) for contrast
- Mood: Cold/precise

## Visual Impression

A mesmerizing display of light splitting into its constituent colors as it passes through simulated optical elements. Electric cyan, warm coral, and golden amber colors dance across a deep navy background, with white glow effects around light sources creating depth and visual interest. The chromatic aberration creates rainbow patterns that shift and flow, revealing the hidden spectrum within white light.

## Parameters

- NUM_RAYS = 15000 (rays traced per light source)
- NUM_OPTICAL_ELEMENTS = 15 (convex lenses, prisms, concave lenses)
- MAX_BOUNCES = 4 (maximum ray bounces)
- DISPERSION_STRENGTH = 0.25 (chromatic aberration intensity)
- REFRACTION_RED = 1.50 (red refraction index)
- REFRACTION_GREEN = 1.52 (green refraction index)
- REFRACTION_BLUE = 1.54 (blue refraction index)
- 8 white light sources positioned in top area
- Glow radius of 80 pixels around light sources

## Running

```bash
uv run python sketch/chromatic_aberration/main.py
```

## Output

- `preview.png` — 1920×1080 preview image
- Change `SIZE` constant in `main.py` for 3840×2160 output

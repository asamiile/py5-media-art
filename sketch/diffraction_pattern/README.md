# Diffraction Pattern

The hidden order of light revealed through wave interference and diffraction, where mathematical precision creates ethereal beauty.

## Technique

Fraunhofer diffraction simulation using Fourier transform principles. Light passing through apertures creates interference patterns that reveal the wave nature of light itself. The simulation uses 2D FFT to compute the far-field diffraction pattern from multiple apertures (circular, rectangular, and double slit), with each aperture type producing characteristic interference fringes and diffraction rings.

## Color Palette

- Background: Deep midnight navy (#0a0a1a)
- Dominant (60%): Electric cyan (#00d4ff) with varying intensity
- Secondary (30%): Warm coral (#ff6b6b) for contrast
- Accent (10%): Golden amber (#ffd93d) for highlights
- Mood: Cold/precise

## Visual Impression

A mesmerizing display of concentric diffraction rings and interference fringes that pulse with mathematical precision, where the wave nature of light creates intricate patterns of bright and dark bands that seem to breathe with ethereal energy. Electric cyan, warm coral, and golden amber colors dance across a deep navy background, with the characteristic Airy disks of circular apertures and the distinctive interference patterns of double slits creating a visual symphony of wave optics.

## Parameters

- GRID_SIZE = 512 (simulation grid resolution)
- NUM_APERTURES = 12 (number of apertures: circular, rectangular, double slit)
- DIFFRACTION_SCALE = 0.5 (scale of diffraction pattern)
- INTENSITY_SCALE = 2.0 (intensity scaling factor)
- Aperture types: circular (Airy disk pattern), rectangular (sinc function pattern), double slit (Young's interference pattern)
- Power-law brightness mapping (intensity^0.5) for contrast enhancement

## Running

```bash
uv run python sketch/diffraction_pattern/main.py
```

## Output

- `preview.png` — 1920×1080 preview image
- Change `SIZE` constant in `main.py` for 3840×2160 output

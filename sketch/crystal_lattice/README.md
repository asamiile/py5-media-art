# crystal_lattice

**X-ray Diffraction: The Hidden Geometry of Matter**

## Concept

The invisible geometric order hidden inside matter — atoms arranging themselves into a perfect lattice, revealed through X-ray diffraction spots that betray the deep symmetry within.

## Technique

- 2D crystal lattice with randomly selected symmetry (hexagonal, square, rectangular, or oblique)
- Reciprocal lattice computation via Fourier transform of real-space basis vectors
- Structure factor calculation with multi-atom basis and genuine phase summation
- Debye-Waller thermal damping for physically realistic intensity falloff
- Concentric Laue zone rings mark constant |G| shells
- Gaussian spot rendering with intensity-driven size and color gradient

## Palette

| Role | Color | Description |
|------|-------|-------------|
| Background | `#060710` | Deep midnight |
| Dominant | `#1A2944` | Sapphire blue |
| Secondary | `#40E0D0` | Electric cyan |
| Accent | `#FFF5D6` | Warm white-gold |

## Parameters

- **Lattice type**: randomly chosen per run (hexagonal / square / rectangular / oblique)
- **Basis atoms**: 2–3 atoms with random fractional coordinates
- **Resolution**: 1920×1080 (preview) / 3840×2160 (output)

## How to Run

```bash
uv run python sketch/crystal_lattice/main.py
```

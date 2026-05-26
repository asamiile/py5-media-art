# sumi_ink_dissolution

A 2D diffusion-advection simulation of ink drops dissolving in still water — a digital sumi-e (ink wash).

## Concept

The ephemeral beauty of a single drop of ink surrendering to water — watching structure dissolve into ghostly plumes that curl, branch, and disappear. Multiple drops are introduced over time, each blooming into organic tendrils via curl-noise advection and Gaussian diffusion.

## Technique

- **Simulation**: 960×540 density field with Laplacian diffusion and semi-Lagrangian advection
- **Curl Noise**: Multi-octave sine interference pattern creating organic swirling flow fields
- **Color Mapping**: Four-zone weighted blend (parchment → sepia wash → deep indigo → sumi black)
- **Paper Texture**: Gaussian-smoothed random noise for subtle washi paper effect
- **Substeps**: 4 simulation passes per render frame for dramatic dissolution

## Palette

| Role | Color | Description |
|------|-------|-------------|
| Background | (245, 238, 228) | Warm parchment |
| Dominant | (15, 12, 18) | Sumi ink black |
| Secondary | (130, 105, 82) | Warm sepia wash |
| Accent | (40, 30, 75) | Deep indigo |

## Output

- **Format**: Animation, 15s @ 60fps
- **Resolution**: 3840×2160 (4K)
- **File**: `sumi_ink_dissolution.mp4`

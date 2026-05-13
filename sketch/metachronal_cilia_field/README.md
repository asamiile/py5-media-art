# metachronal_cilia_field

A 10 second animation of microscopic cilia moving in metachronal waves. Short comb-like filaments bend out of phase across a dim biological membrane, producing diagonal bands of pearl and cyan flow with faint coral afterimages.

## Technique

- Procedural phase field for cilia beat timing and recovery.
- Vectorized comb-ridge synthesis creates thousands of short filament strokes without per-stroke drawing.
- Flow memory accumulates from local shear and decays into soft coral traces.
- Encoded with FFmpeg as `output.mp4` and mirrored to `metachronal_cilia_field.mp4`.

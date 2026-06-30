# Kinetic Fiber Optic String Weaving 2D

**Date**: 2026-06-30
**Type**: Animation (450 frames, 30fps)
**Output Resolution**: 3840x2160 (4K)

## Concept
A kinetic visualization of thousands of glowing fiber optic strings weaving a complex geometric tapestry. The lines trace along the boundaries of the canvas, continuously shifting their anchor points to generate an intricate, breathing moiré and 3D illusion in the center.

## Technical Details
- **Rendering Pipeline**: The artwork generates dense geometry (over 6,000 intersecting translucent lines per frame). Because this creates an extremely heavy, uncompressible additive noise field, Java's internal PNG encoder stalls and hangs at 4K resolution.
- **Optimization**: To resolve this bottleneck, the artwork is rendered internally by `py5` at `1920x1080` and the frames are saved directly as uncompressed `.tif` files. This bypasses the Java compression overhead entirely.
- **Upscaling**: FFMPEG compiles the `.tif` image sequence and simultaneously applies a hardware-accelerated `-vf scale=3840:2160` filter, producing a pristine, flawless 4K `.mp4` video without crashing the JVM.
- **Geometry**: The strings are drawn via NumPy vectorized arrays processed instantly through `py5.begin_shape(py5.LINES)`. 

## Palette
- **Background**: Deep charcoal `#111111`
- **Flares**: Electric red and bright magenta borders
- **Interference**: Intense additive white glowing strings in the core

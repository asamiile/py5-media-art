# generative_slit_scan_glitch_landscape_2d

## Concept
An intense, colorful moving landscape generated using digital slit-scan techniques, evoking a feeling of driving through a neon, glitched 80s cyberpunk city at hyper-speed.

## Technique
A full 4K buffer is maintained directly in a NumPy array. Each frame, the array is shifted to the left by 20 pixels, and a new 20-pixel column of glitchy, mathematically generated "noise" (created from interfering sine and cosine fields) is injected on the right edge. Scanlines and thresholding are applied to make it look like a corrupted retro screen. The numpy array is instantly drawn to the py5 canvas using `py5.create_image_from_numpy`.

## Palette
- **Background**: Glitchy black scanlines
- **Primary**: Neon pink/red and bright cyan
- **Mood**: Fast, retro, corrupted, intense

## Format
Animation (450 frames @ 30fps)

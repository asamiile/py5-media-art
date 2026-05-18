# Cellular Division Bloom

A microscopic visualization of cells dividing and multiplying in a petri dish, creating elegant fractal-like branching patterns as populations expand exponentially.

## Visual Concept

A single cell appears at center and immediately divides into two. Those divide into four, four into eight, creating a cascade of exponential growth. Cells pulse rhythmically as they prepare to divide, creating a living, breathing pattern. The symmetrical branching structure fills the canvas with organic mathematical elegance.

## Technical Details

- **Format**: Animation (16s @ 60fps, 4K/3840×2160)
- **Algorithm**: Recursive cell division system with generation-based lifecycle
- **Technique**: 
  - Recursive branching with decreasing cell size per generation
  - Age-based triggering of cell division (60% of lifespan)
  - Directional propagation based on parent angle
  - Size scaling: radius = 20 - generation×2.5
  - Pulsing radius animation with sine-wave modulation
  - Generation-depth color mapping with alternating hue shifts
  - Nucleus rendering for early-generation cells

## Color Palette

- **Background**: Laboratory white (#f5f5f0)
- **Dominant (60%)**: Biotic green (#00bb44) to emerald (#00cc66)
- **Secondary (30%)**: Cyan with translucent highlights (#00dddd)
- **Accent (10%)**: Deep purple cell nuclei (#330066)
- **Mood**: Organic/Precise with biotech aesthetic

## Conceptual Theme

This work visualizes authentic cellular biology—division and exponential growth—through procedural generation. Rather than simulating physics, it explores the mathematical patterns inherent in life itself: exponential branching, size scaling, and recursive self-similarity.

The biological theme fills a gap in the collection, distinct from computational networks, natural disasters, and physical phenomena, while maintaining the mathematical elegance central to generative art.

# Fractal Tree Generation

A recursive visualization of natural tree growth using Lindenmayer systems (L-systems), showing how simple branching rules create complex botanical structures.

## Visual Concept

A single trunk erupts and immediately splits into two branches. Each branch splits again, recursively creating a fractal tree. Brown woody branches grow progressively thinner with each generation while glowing green leaves bloom along the structure, creating a living fractal visible on screen.

## Technical Details

- **Format**: Animation (14s @ 60fps, 4K/3840×2160)
- **Algorithm**: Recursive L-system tree generation with turtle graphics rendering
- **Technique**:
  - 10-generation binary branching from central trunk
  - Angle-based splitting (±0.4 radians from parent angle)
  - Length scaling (75% per generation)
  - Thickness scaling with generation depth
  - Progressive animation revealing generation by generation
  - Generation-based color mapping (warm browns)
  - Leaf particle effects on mature branches

## Color Palette

- **Background**: Forest midnight black (#0a0a0a)
- **Dominant (60%)**: Dark wood brown (#2d1810) to warm sienna (#8b4513)
- **Secondary (30%)**: Bioluminescent leaf green (#00dd55)
- **Accent (10%)**: Golden branch highlights (#ffaa33)
- **Mood**: Organic/Warm with growth energy

## Conceptual Theme

This work visualizes the fractal nature of trees—how recursive simple branching rules generate complex botanical structures. Rather than simulating physics, it emphasizes the mathematical elegance inherent in nature's growth patterns.

The L-system approach is mathematically rigorous while remaining visually organic and authentic to real tree morphology. Distinct from cellular division (single cells) and computational networks by focusing on macro-scale botanical growth.

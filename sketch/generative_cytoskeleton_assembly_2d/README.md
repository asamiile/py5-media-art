# generative_cytoskeleton_assembly_2d

Visualizing the dynamic assembly and disassembly of a cellular cytoskeleton (microtubules and actin filaments) (inspired by GO:0007010).

## Details

- **Type**: 2D animation
- **Length**: 10 seconds (60fps)

## Technique

A 2D simulation using 8000 short line segments (filaments) colored green (microtubules) and red (actin). The filaments align their angles to a multi-octave Perlin noise flow field and slowly drift. A secondary noise field modulates the `current_len` of each filament, simulating rapid polymerization and depolymerization as they move through different chemical gradients. Rendered with additive blending and a fading background to create fluid trails.

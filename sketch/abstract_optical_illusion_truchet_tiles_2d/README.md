# abstract_optical_illusion_truchet_tiles_2d

## Concept
An optical illusion of constantly shifting mazes and loops. Thousands of individual Truchet tiles rotate dynamically to organically assemble and disassemble massive interconnected paths.

## Technique
The 4K canvas is filled with over 2,000 Truchet tiles (arcs on an invisible square grid). Rather than rotating them randomly, their rotation angles are smoothly driven by a seamless 2D spatial Perlin noise loop. When `py5.noise()` evaluates between certain thresholds, the tile snaps its rotation by 90-degree increments. To add dynamic kinetic energy to the piece, a "smooth flip" animation is implemented using a Smoothstep ease-function, making the tiles physically spin quickly into their new rotation states when the noise wave washes over them.

## Palette
- **Canvas**: A high-contrast monochrome design. The background is an off-white `#EFEFEF` paper color, and the thick Truchet lines are drawn in dark charcoal `#222222`. 
- **Accent**: Occasionally, vibrant glowing neon-orange circles pop into existence at the tile intersections based on the noise field.
- **Mood**: Complex, shifting, geometric, kinetic

## Format
Animation (450 frames @ 30fps)

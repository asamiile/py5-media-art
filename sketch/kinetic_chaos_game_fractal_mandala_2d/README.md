# kinetic_chaos_game_fractal_mandala_2d

## Concept
An animated and kaleidoscopic take on the "Chaos Game", a mathematical process that draws geometric fractals (like the Sierpinski pentagon) through millions of localized point jumps towards random vertices.

## Technique
Instead of letting a single point jump millions of times (which would take too long per frame in Python), this sketch initializes an array of 500,000 points in NumPy. Every frame, these 500k points simultaneously pick a random target vertex and jump towards it. By animating the position of the vertices (a slow rotation) and smoothly oscillating the jump distance modifier using sine waves, the structure breathes and morphs continuously. The points are drawn with heavy transparency using `py5.blend_mode(ADD)`, leaving beautiful glowing density histograms.

## Palette
- **Background**: Faint fading black
- **Points**: Additive blend colors grouped by their target vertex (Red, Green, Blue, Yellow, Cyan)
- **Mood**: Mathematical, cosmic, breathing, intricate

## Format
Animation (450 frames @ 30fps)

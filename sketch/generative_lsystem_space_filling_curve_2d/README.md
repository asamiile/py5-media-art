# Generative L-System Space-Filling Curve

An animated 15s sequence of a dragon curve fractal drawing itself.

## Concept

- **Theme**: A space-filling curve (the Dragon curve) that incrementally draws itself, leaving a glowing trail that fades over time to reveal the complex geometry of the fractal.
- **Technique**: A parameterized L-System expanded in Python into 14 iterations, producing thousands of drawing instructions. The line segments are then drawn incrementally over time in Py5 using scaled translations and additive blending.
- **Palette**: Bright emerald and sapphire on a pitch-black background, cycling rapidly as the path draws.

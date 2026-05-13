# eutectic_alloy_solidification

A py5 animation of a cooling eutectic alloy freezing into alternating lamellae, grain boundaries, and copper-rich impurity channels.

The sketch renders a low-resolution vectorized solidification field directly into the py5 pixel buffer, then saves 600 frames and encodes a 10 second 4K/60fps `output.mp4`.

Generated media:

- `eutectic_alloy_solidification_p1.png` - preview frame
- `output.mp4` - generated animation output, not committed unless explicitly requested
- `frames/` - generated frame sequence, ignored by git

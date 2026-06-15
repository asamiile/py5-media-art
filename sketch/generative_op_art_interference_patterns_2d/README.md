# generative_op_art_interference_patterns_2d

An animated 15s sequence of high-contrast black and white optical art, featuring moving concentric shapes that create moiré and interference patterns.

## Theme
A high-contrast black and white optical art animation, inspired by Bridget Riley or Victor Vasarely, using moving concentric shapes and grids that create moiré and interference patterns.

## Technique
A base layer of thick concentric circles is drawn statically. A second layer of matching concentric circles is drawn over it, offset by slow-moving sine and cosine waves based on time. `py5.DIFFERENCE` blend mode is used, meaning overlapping white lines invert the underlying black lines, creating a harsh, high-contrast strobing moiré effect. A rotating starburst of radial lines is added to maximize the optical illusion.

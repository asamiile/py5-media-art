# generative_abelian_sandpile_fractal_2d

## Concept
The Abelian Sandpile Model produces incredibly intricate, Persian-rug-like fractal patterns. When a massive number of virtual "sand grains" are dropped into the center of a grid, any cell that accumulates 4 or more grains topples over, sending exactly 1 grain to each of its 4 cardinal neighbors. As the toppling cascades outward, complex, perfectly symmetrical geometric patterns naturally emerge.

## Technique
Because toppling cascades can easily take billions of iterations in Python, this sketch completely vectorizes the logic using 2D NumPy array masks and `np.roll` shifts. The simulation runs 250 topple steps per frame. Over 15 seconds, millions of sand grains are dropped into the center, generating a spectacular expanding fractal mapped to a neon color palette.

## Palette
- **0 grains**: Deep Space Blue
- **1 grain**: Neon Pink
- **2 grains**: Bright Orange
- **3 grains**: Electric Cyan
- **Mood**: Complex, crystalline, symmetrical, fractal

## Format
Animation (450 frames @ 30fps)

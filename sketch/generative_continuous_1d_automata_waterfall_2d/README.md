# generative_continuous_1d_automata_waterfall_2d

An abstract procedural animation depicting a continuously falling waterfall of digital data, generated using a continuous-state 1D cellular automaton.

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
Unlike traditional cellular automata (such as Conway's Game of Life or Wolfram's Rule 30) which use discrete binary states (0 or 1), this sketch utilizes continuous floating-point values between 0.0 and 1.0. 
Each frame, the top row of the screen is updated using a 1D convolution kernel ($W_{left}, W_{center}, W_{right}$) that continuously shifts its weights based on trigonometric time functions. The resulting value is passed through a non-linear fractal folding activation function ($val = val - \lfloor val \rfloor$) to keep it bounded while creating chaotic, intricate interference patterns. The entire matrix is shifted downwards, creating a cascading waterfall effect.
The internal float matrix runs at 1920x1080 for high performance and is directly color-mapped using a vectorized sine-wave RGB palette, before being seamlessly scaled up to 4K resolution using `py5.image()`.

# generative_liquid_metal_interference_2d

Simulating the psychedelic interference patterns of light reflecting off liquid metal or an oil slick.

## Details

- **Type**: 2D animation
- **Length**: 10 seconds (60fps)

## Technique

Utilizing `py5.os_noise` with high octaves and frequency mapped directly to hue and brightness across a dense grid of rectangles. A sine wave function is wrapped around the noise values to create sharp interference banding typical of thin-film iridescence.

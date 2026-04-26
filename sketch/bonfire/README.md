# Bonfire

Fractal noise domain-warping generates organic flame tongues rising from a glowing base. A meditation on chaos organized by rising heat.

## Concept

Fire is one of the most visually complex natural phenomena: simultaneously ordered (heat always rises) and chaotic (each flame tongue is unique). This work captures that duality by letting a fractal noise field define flame shapes, then distorting it with a second warp layer to create the characteristic sideways-flickering turbulence of real fire.

## Technique

- **Domain warping**: Two layers of fBm noise shift the x-coordinate of the base heat field, creating the irregular lateral oscillation of flame tongues
- **Base heat field**: 5-octave fBm noise on the warped coordinates defines raw flame structure  
- **Vertical taper**: Power-law falloff (exponent 0.45) allows flames to reach ~75% up the canvas while fading naturally at the tips
- **Horizontal focus**: Height-dependent Gaussian envelope narrows toward the top, shaping the fire into a bonfire column
- **Palette**: Eight-zone mapping: black → deep crimson → orange → amber → near-white (the classic fire progression)
- **fBm**: Implemented as superposed sine/cosine harmonics with random phases per octave

## Color Palette

- **Black** — void beyond the flame
- **Deep crimson** `#A00000` — dim outer flame and tips
- **Orange** `#FF5000` — mid-intensity flame body
- **Amber/yellow** `#FFB000` — hot flame core
- **Near-white** `#FFFFD2` — white-hot center regions

## Notes

- Static image; each run produces a unique fire configuration (no fixed random seed)
- Canvas: 1920×1080 preview | 3840×2160 output-ready
- Pure numpy + PIL — no OpenCV or scipy dependency

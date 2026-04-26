# Stellar Nursery

A deep-sky image of a stellar nursery — interstellar gas and dust collapsing under gravity, lit from within by newly-born protostars, rendered in the narrowband emission palette used by professional astrophotography.

## Concept

Star formation happens inside vast molecular clouds where cold gas condenses into knots of increasing density until nuclear fusion ignites. This work simulates the visual signature of that process: hydrogen-alpha emission from ionized gas, oxygen-III teal from hotter ionization fronts, sulfur-II amber from dense knots — the same spectral lines captured by the Hubble Space Telescope.

## Technique

- **Gas density**: Three fBm (fractional Brownian motion) noise layers at different scales — large-scale structure, mid-scale filaments, fine wisps — combined and contrast-enhanced
- **Dust lanes**: Separate fBm field modulates density to create dark absorption silhouettes
- **Emission channels**: Independent fBm fields for Hα, OIII, and SII with distinct spatial distributions
- **Protostars**: 5–11 embedded point sources with sharp cores + wide power-law halos illuminating surrounding gas
- **Background stars**: 800–1500 background stars with color temperature variation, dimmed by local dust extinction
- **Bloom**: Multi-scale Gaussian convolution (σ=2, 8, 25) simulates telescope diffraction and glow
- **Tone mapping**: HDR exponential tone map (`1 − e^(−1.8x)`) compresses the wide dynamic range to display values

## Color Palette

Based on the Hubble Palette (SII-Hα-OIII mapping):
- **Hα red** `#DA1F38` — hydrogen-alpha emission (ionized hydrogen)
- **OIII teal** `#148094` — doubly-ionized oxygen (hotter ionization fronts)
- **SII amber** `#D4943A` — singly-ionized sulfur (denser, cooler knots)
- **Star white** `#F2EBD9` — protostar cores
- **Background** `#050214` — cosmic void

## Notes

- Static image generated entirely with numpy; PIL saves the final frame directly
- No fixed random seed — each run produces a unique nebula
- Canvas: 1920×1080 preview | 3840×2160 output-ready

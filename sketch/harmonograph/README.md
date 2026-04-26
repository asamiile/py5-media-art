# harmonograph

**Theme**: "Fading resonance" — a dual-pendulum mechanical plotter; the exponentially decaying oscillations trace an inward-spiraling figure as the machine winds down from wild swings to a final rest

**Technique**: Two-component x and two-component y pendulum formula (x(t) = Σ aᵢ·sin(fᵢt+pᵢ)·exp(−dᵢt)); random near-rational frequency ratios near 2:3 produce closed Lissajous-like envelopes that precess and spiral; age-based color gradient maps early trace (bright gold) through late (dark amber) to dead center (near-black); randomized phases and frequencies produce a unique form every run

**Description**: 500k points trace the full life of the harmonograph: at t=0 both pendulums swing at full amplitude tracing a wide golden figure; as the exponential decay takes over the loops tighten and the color darkens to amber, the trace converging toward the center. The resulting twisted-ribbon form encodes the physics of coupled oscillators in a single image.

**Palette**:
- Background: `#050409` near-black
- Early trace: `#e1af37` warm gold
- Late trace: `#3a280c` dark amber
- Dead center: `#08060e` near-background

**Preview**: `preview.png`

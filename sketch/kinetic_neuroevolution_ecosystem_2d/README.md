# kinetic_neuroevolution_ecosystem_2d

A 4K kinetic visualization of a neuroevolution ecosystem — microscopic creatures equipped with tiny feedforward neural networks compete for survival in a bioluminescent void. Intelligence emerges purely from the pressure of hunger and reproduction.

## Concept

Each creature carries a neural network brain (15 sensors → 10 hidden → 2 outputs) that controls its movement. Creatures sense nearby food through 15 directional sensors arranged 360° around their body. Based on sensor activation, the network outputs a movement angle and magnitude. Creatures that find food efficiently survive longer, reproduce more often, and pass their neural weights to offspring with small random mutations — natural selection in action.

## Techniques

- **Neuroevolution**: Feedforward neural networks (15→10→2) evolved via reproduction + mutation (rate 12%)
- **Directional sensing**: 15 radial sensors detect food proximity at configurable range
- **Population dynamics**: Birth, starvation death, max population cap (400 creatures)
- **Genetic lineage coloring**: Hue encodes genetic family; health maps teal → crimson
- **NumPy vectorized NN**: Fast batch feedforward computation per frame
- **Real-time HUD**: Population count, birth/death tallies, avg health, population history sparkline
- **Toroidal world**: Screen-edge wrap-around for seamless creature movement

## Parameters

| Parameter | Value |
|---|---|
| Simulation resolution | 960 × 540 (upscaled to 4K) |
| Initial population | 80 creatures |
| Max population | 400 creatures |
| Food sources | 20 pellets (regenerating) |
| Sensor range | 60 sim-units |
| Health decay | 0.18/frame |
| Reproduction prob. | 0.06% / frame (health > 60) |
| Mutation rate | 12% per weight |
| Animation | 20s @ 60fps (1200 frames) |

## Palette

- **Background**: Deep Obsidian Void
- **Creatures (healthy)**: Bioluminescent Aquamarine / Teal
- **Creatures (dying)**: Crimson / Electric Magenta
- **Food pellets**: Solar Amber Gold
- **Sensor rays**: Yellow-White (active) / Dim Indigo (inactive)

## Output

- `kinetic_neuroevolution_ecosystem_2d.mp4` — 4K 60fps 20-second animation
- `kinetic_neuroevolution_ecosystem_2d_p1.png` — Mid-animation preview frame

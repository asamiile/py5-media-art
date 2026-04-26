# Mycelium Network

A generative visualization of underground fungal growth patterns, rendered as delicate branching networks spreading through dark soil.

## Concept

This work simulates mycelium networks—the vegetative part of fungi that decomposes organic matter and connects plants in forest ecosystems. Each thread grows, branches, and ages, creating the visual impression of an interconnected underground kingdom where life works silently.

## Technique

- **Growth algorithm**: Stochastic branching with physics-based random walk
- **Seed distribution**: 15 initial growth points distributed across the canvas
- **Branching logic**: Probability increases with age, encouraging mature threads to split
- **Color mapping**: Cream (new/active) → Brown (mature/aged) as threads age
- **Visual effects**: Faint glow surrounding young growth tips to emphasize active growth zones
- **Depth perception**: Stroke weight tapers with branching depth to suggest 3D structure

## Color Palette

- **Background**: Deep charcoal (#191919) — soil darkness
- **New growth**: Cream (#F0EBCB) — fresh, active mycelium
- **Mature threads**: Burnt brown (#6E461E) — aged mycelium
- **Glow accent**: Pale cream with transparency — growth activity

## Iterations

- **v1**: Initial implementation with sparse networks and basic color transitions
- **Final**: Denser networks (15 seed points), extended growth duration, glow effects for visual impact

## Technical Notes

- Canvas: 1920×1080 (preview) | 3840×2160 (output-ready)
- Simulation duration: ~120 frames at 60fps (2 seconds before capture)
- Each thread lives up to 400 frames; branching probability: 6% baseline + 0.02% per frame age
- No fixed random seed; results vary per run

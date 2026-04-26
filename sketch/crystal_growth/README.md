# crystal_growth

**The slow persistence of mineral crystallization**

![preview](preview.png)

## Concept

Order emerging from chaos at geological timescales — multiple seed points in cave darkness sprout dendritic crystal arms that branch at crystallographic angles (60°/90°), each sub-branch spawning further dendrites until the structure fills space like frozen lightning.

## Technique

- **Stochastic branching growth** — Each seed emits 4–7 primary arms that grow with Brownian angular deflection
- **Crystallographic angle constraints** — Sub-branches spawn at preferred angles (60°, 90°, 30°) mimicking real mineral crystal lattice orientations
- **Depth-controlled branching** — Branch probability and length decay exponentially with depth (up to 8 levels)
- **Anti-aliased line segments** — Continuous thick lines drawn between consecutive positions for smooth rendering
- **Multi-scale glow** — 5-sigma Gaussian blur layers create atmospheric luminosity around the crystal structure
- **Age-based color gradient** — 4-stop palette encodes growth age from deep violet core → amethyst → quartz rose → mineral gold tips

## Palette

| Role | Color | Description |
|------|-------|-------------|
| Background | `rgb(12, 12, 18)` | Cave darkness |
| Core | `rgb(68, 42, 100)` | Deep violet |
| Dominant | `rgb(138, 92, 168)` | Amethyst |
| Secondary | `rgb(195, 155, 170)` | Quartz rose |
| Tips | `rgb(212, 185, 120)` | Mineral gold |

## Parameters

- 3–5 random seed points per run
- Up to 8 branching depth levels
- ~200k line segments per render
- Each run produces a unique crystalline structure

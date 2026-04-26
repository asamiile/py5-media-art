# ink_diffusion

**The quiet moment when ink meets wet paper**

![preview](preview.png)

## Concept

Sumi-e ink wash bleeding on washi paper. Multiple ink drops release particles that undergo Brownian motion along paper fiber direction, accumulating density trails that fray into gossamer tendrils. Drops interact through connecting flows and satellite spatters add natural imperfection.

## Technique

- **Stochastic particle diffusion** — 60k particles per drop undergo Brownian random walks
- **Fiber-direction anisotropy** — Global paper grain direction stretches diffusion along one axis, simulating how real ink follows washi fibers
- **Variable concentration** — Each drop has a randomized ink concentration (0.3–1.0), creating natural tonal variation from dilute washes to dense pools
- **Inter-drop tendrils** — Nearby drops spawn flow particles that create connecting ink bridges
- **Satellite splatter** — Tiny secondary drops scatter around main impacts for authentic imperfection
- **Log-scale tone mapping** — Density field mapped through log + gamma curve for ink-like tonal response
- **Three-stop color gradient** — Parchment → warm grey (with indigo tint) → sumi ink black

## Palette

| Role | Color | Description |
|------|-------|-------------|
| Background | `rgb(245, 240, 232)` | Warm parchment |
| Mid-tone | `rgb(107, 101, 96)` + `rgb(58, 61, 92)` | Warm grey with indigo wash |
| Ink | `rgb(26, 26, 26)` | Sumi ink black |

## Parameters

- 5–8 random ink drops per run
- 800 diffusion steps
- Paper fiber angle: random slight tilt from horizontal
- Each run produces a unique composition

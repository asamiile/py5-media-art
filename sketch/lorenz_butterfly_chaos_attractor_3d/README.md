# lorenz_butterfly_chaos_attractor_3d

A 20-second animation of 4,000 simultaneous particles tracing the Lorenz strange attractor — chaos that is infinitely complex yet always bounded, forming ghostly butterfly wings in the dark.

## Concept

The Lorenz system (σ=10, ρ=28, β=8/3) is the canonical example of deterministic chaos: three simple differential equations whose solutions never repeat yet never escape. All 4,000 particles start from nearly identical initial conditions; by the end, sensitive dependence on initial conditions has spread them across the full butterfly.

## Technique

- **Physics**: Vectorized numpy Euler integration of the Lorenz ODE, 3 sub-steps per frame at dt=0.005
- **Rendering**: CPU pixel-buffer with additive blending; each frame decays by 97% toward background (trail persistence)
- **Coloring**: Velocity magnitude → thermal gradient: navy (slow) → cobalt → cyan → hot-white → amber-orange (fast)
- **Camera**: Slow Y-axis rotation + subtle X wobble, simulated via 3D rotation matrices projected to 2D

## Color Palette

- Background: Deep near-black navy `#03030C`
- Slow particles: Cobalt blue → electric cyan
- Fast particles: Hot white → amber orange
- Mood: Dark/Moody

## Format

Animation — 20s @ 60fps, 3840×2160

# kinetic_kuramoto_firefly_sync_2d

A 4K kinetic visualization of the **Kuramoto model** of coupled phase oscillators, rendered as a bioluminescent firefly swarm spontaneously synchronizing. 300 fireflies drift through the void, each pulsing at its own natural frequency. As the coupling constant K slowly rises above the critical threshold K_c ≈ 1.6, the chaos of independent rhythms suddenly collapses into a single coherent pulse — the most beautiful phase transition in nature.

## Concept

The Kuramoto model (1975) describes how N coupled oscillators achieve spontaneous synchronization. Each oscillator i has a natural frequency ω_i drawn from a Gaussian distribution. The phase θ_i evolves as:

```
dθ_i/dt = ω_i + (K/N) · Σ_j sin(θ_j − θ_i)
```

Below the critical coupling K_c = 2σ_ω ≈ 1.6, oscillators remain incoherent (R ≈ 0). Above K_c, a fraction of oscillators lock together, and R rises sharply — a second-order phase transition. By K = 3.2, the system reaches R ≈ 0.96: near-perfect global synchrony.

This is the mathematical explanation for synchronized firefly flashing, cardiac pacemaker cells, and neural rhythms.

## Visualization

- **300 fireflies** drift across a 960×540 sim grid (upscaled to 4K)
- Each firefly's **color** encodes its natural frequency: blue/violet (slow) → green → amber/red (fast)
- Each firefly **flashes** when its phase θ passes through 0 (modulo 2π)
- Flash **brightness** is modulated by `cos(θ)³` — sharp pulse at peak
- **Trail persistence** (α=0.88) creates motion blur and firefly trails
- A central **mean-field arrow** (golden) shows the order parameter direction ψ
- **K coupling bar** ramps from 0.0 → 3.2 over 20 seconds

## Phase Transition Timeline

| Time | Frame | K | R | State |
|------|-------|-----|-----|-------|
| 0s   | 0     | 0.0 | ~0.05 | Chaos — independent rhythms |
| 7s   | 420   | 1.1 | ~0.10 | Subcritical — weak correlation |
| 10s  | 600   | 1.6 | ~0.35 | **Critical threshold K_c** |
| 15s  | 900   | 2.4 | ~0.91 | Supercritical — mass synchrony |
| 20s  | 1200  | 3.2 | ~0.96 | Full sync — unified pulse |

## Techniques

- **Kuramoto model**: N×N vectorized phase coupling (`thetas[None,:] - thetas[:,None]`)
- **NumPy matrix operations**: O(N²) coupling computed as single array operation
- **Float32 trail buffer**: Soft additive accumulation with per-frame decay
- **Gaussian glow**: `exp(-dist² / r²)` soft disk rendered per firefly
- **Flash modulation**: `max(0, cos(θ))³` creates sharp, naturalistic pulse
- **Signed int32 ARGB blit**: Direct pixel write to Py5Image buffer

## Parameters

| Parameter | Value |
|---|---|
| N oscillators | 300 |
| σ_ω (freq spread) | 0.8 |
| K range | 0.0 → 3.2 |
| Critical K_c | ≈ 1.6 |
| Integration dt | 0.06 |
| Animation | 20s @ 60fps |
| Output | 4K (3840 × 2160) |

## Output

- `kinetic_kuramoto_firefly_sync_2d.mp4` — 4K 60fps 20-second animation
- `kinetic_kuramoto_firefly_sync_2d_p1.png` — Mid-animation preview (K≈1.6, at phase transition)

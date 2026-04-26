# lorenz_attractor

**Theme**: "Convective turbulence" — the Lorenz attractor, born from a 1963 meteorology model, reveals the butterfly where chaos lives

**Technique**: Runge-Kutta 4 integration of the Lorenz ODE system, 800 parallel trajectories, density accumulation, log-scale tone mapping

**Description**: 800 trajectories are simultaneously integrated through the Lorenz system (σ=10, ρ=28, β=8/3) using RK4 at dt=0.004. After a burn-in of 2000 steps, 25,000 steps per trajectory are recorded and projected onto the (x, z) plane — the canonical butterfly view. Point density is accumulated into a 2D histogram, log-mapped, and rendered through a rust→amber→pale-gold palette. The two lobes and their dark hollow centers emerge from the attractor's own geometry.

**Palette**:
- Background: `#020308` near-black
- Low density: `#5a1e08` deep rust
- Mid density: `#c87814` warm amber
- Peak density: `#ffdC8c` pale gold

**Preview**: `preview.png`

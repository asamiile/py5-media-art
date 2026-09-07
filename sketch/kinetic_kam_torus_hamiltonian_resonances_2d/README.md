# kinetic_kam_torus_hamiltonian_resonances_2d

**kinetic_kam_torus_hamiltonian_resonances_2d** is an algorithmic media art animation simulating the non-linear symplectic phase-space geometry of the **Kolmogorov-Arnold-Moser (KAM) theorem** and **Poincaré-Birkhoff resonant island chains**, capturing the persistence of nested invariant tori, adiabatic orbital precession, hyperbolic separatrix bifurcations, and symplectic phase-space particle drift.

## Concept & Celestial Hamiltonian Dynamics

In non-linear Hamiltonian mechanics and celestial orbital resonance (e.g. asteroidal Kirkwood gaps, particle accelerator synchrotrons, and planetary rings), an integrable system governed by action-angle variables $(I, \theta)$ under multi-frequency perturbations obeys:

$$H(\mathbf{I}, \boldsymbol{\theta}, t) = H_0(\mathbf{I}) + \sum_{m} \epsilon_m(\mathbf{I}) \cos(\mathbf{m} \cdot \boldsymbol{\theta} - \Omega_m t)$$

- **Kolmogorov-Arnold-Moser (KAM) Invariant Tori**:
  Tori with sufficiently irrational winding numbers (such as golden-ratio diophantine frequencies) survive non-linear perturbations, forming nested, continuous barrier surfaces that confine phase-space trajectories into beautiful concentric laminar loops.
- **Poincaré-Birkhoff Island Chains**:
  Near rational commensurabilities $\omega_1 / \omega_2 = p / q$, resonant tori break up into chains of alternating elliptic fixed points (resonance island centers) and hyperbolic saddle points (X-points).
- **Hyperbolic Separatrix Loops**:
  Separatrix boundaries encircle each resonant island, delineating the threshold between regular libration and stochastic Arnold diffusion.
- **Symplectic Flow & Phase-Space Sparks**:
  Governed by Hamilton's canonical equations:
  $$\frac{dx}{dt} = \frac{\partial H}{\partial y}, \quad \frac{dy}{dt} = -\frac{\partial H}{\partial x}$$
  The velocity field is strictly divergence-free ($\nabla \cdot \mathbf{v} = 0$, Liouville's theorem), allowing celestial tracer sparks to circulate indefinitely along invariant tori contours without dissipation.

## Visual Composition (60-30-10 Palette)

- **60% Celestial Abyssal Obsidian**: Deep celestial space and potential well depth (`#020309`, `#080618`), representing the unperturbed phase-space vacuum.
- **30% Invariant KAM Tori & Resonant Separatrices**: Luminescent Electric Cyan (`#00f8e1`) and Mint Jade (`#00e6a8`) tracing nested invariant tori, enveloped by Neon Violet and Royal Magenta (`#b824e8`, `#381078`) separatrix loops.
- **10% Elliptic Island Cores & Singularities**: Solar Amber (`#ffd060`) and pure Diamond White (`#ffffff`) marking stable Lagrange resonance cores, central potential extrema, and symplectic tracer sparks.

## Execution

```bash
uv run python sketch/kinetic_kam_torus_hamiltonian_resonances_2d/main.py
```

Outputs:
- 18s @ 60fps (1080 frames) 4K Ultra HD video (`output.mp4` / `kinetic_kam_torus_hamiltonian_resonances_2d.mp4`)
- Preview snapshot: `kinetic_kam_torus_hamiltonian_resonances_2d_p1.png`

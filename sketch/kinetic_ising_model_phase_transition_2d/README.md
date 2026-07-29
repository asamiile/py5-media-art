# kinetic_ising_model_phase_transition_2d

**Date**: 2026-07-24
**Type**: Animation (900 frames, 60fps)

## Concept
A statistical physics simulation of ferromagnetism using the 2D Ising Model. The system's temperature slowly oscillates around the critical point (T_c ≈ 2.269) over the course of the animation. Below this threshold, aligned magnetic domains grow into massive, fractal island structures spanning the entire lattice. Above it, thermal fluctuations shatter any order into chaotic noise. Passing through the critical point itself reveals the scale-invariant, self-similar domain boundaries characteristic of a second-order phase transition.

## Techniques
- **Metropolis-Hastings Algorithm**: Each spin update follows the Metropolis criterion: a spin flip is always accepted if it lowers the system's energy (ΔE ≤ 0), and accepted probabilistically with weight `exp(-β·ΔE)` if it raises energy. This satisfies detailed balance, ensuring the system ergodically samples the correct Boltzmann distribution at any temperature.
- **Vectorized Checkerboard Update**: On a standard Ising lattice, updating spins simultaneously is invalid because adjacent spins influence each other's flip decision. This simulation resolves the conflict by splitting the grid into an even/odd checkerboard pattern. All even-sublattice spins are updated simultaneously (their neighbors are all odd, and remain frozen), then all odd-sublattice spins are updated. This allows full NumPy vectorization across the entire grid without sequential loops.
- **Precomputed Flip Probabilities**: The change in energy ΔE for any single spin flip on a square lattice is constrained to the discrete set {-8, -4, 0, 4, 8}. Only the positive values require a probabilistic decision. The two acceptance probabilities `exp(-β·4)` and `exp(-β·8)` are computed once per physics step and reused for the entire grid, avoiding redundant exponential evaluations.
- **Temperature Oscillation Through T_c**: The temperature follows `T = 2.269 + 1.2·sin(2πt)`, sweeping between approximately 1.07 (deep ferromagnetic order) and 3.47 (disordered paramagnetic phase) over one full animation cycle. Passing through the critical point in both directions makes the divergence of the correlation length — and the emergence of self-similar domain structure — directly visible.
- **Pixel Upscaling**: The physics simulation runs on a reduced grid (screen dimensions divided by `SCALE = 4`), then each cell is expanded to a 4×4 pixel block via `np.repeat`. This gives the simulation a deliberate pixel-art aesthetic while keeping the physics grid computationally manageable, and ensures the domain boundaries read as clean, bold edges rather than aliased noise.
- **Direct Pixel Buffer Write**: The spin array is mapped directly into the `np_pixels` buffer each frame without any intermediate drawing calls. The ARGB values are constructed in a NumPy array and assigned in a single operation, making the rendering step essentially free relative to the physics computation.

## Palette
Spins in the `+1` (up) state are rendered as **Cyan** (RGB 0, 255, 255). Spins in the `-1` (down) state are rendered as **Magenta** (RGB 255, 0, 255). The binary, high-contrast palette makes the domain structure unambiguous at any phase: the viewer can immediately read the degree of order from the average domain size and boundary sharpness without any additional visual encoding.

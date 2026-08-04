# kinetic_physarum_slime_mold_network_2d

A 4K kinetic visualization of Jeff Jones' agent-based model of *Physarum polycephalum* (slime mold) demonstrating self-organizing path networks. 80,000 autonomous sensory agents split into 3 distinct species traverse a 1280×720 simulation space (upscaled to 4K), depositing chemical trails that diffuse and decay. The colony dynamically shapes, optimizes, and rewires its bioluminescent transport highways to connect 6 orbiting food attractors.

## Concept

*Physarum polycephalum* is a unicellular, multi-headed slime mold capable of solving complex pathfinding problems (such as the Tokyo subway network) without any centralized brain. 

This simulation models the emergent intelligence of slime mold:
- **Sensing**: Each agent has three forward-facing sensors (Left, Center, Right) that sample the local pheromone trail concentration. Agents turn towards the highest concentration.
- **Deposition**: As agents move, they deposit pheromones on the grid.
- **Diffusion & Decay**: Pheromones diffuse outward over time and evaporate, encouraging the emergence of optimal, shortened path networks.
- **Heterogeneous Species**: 3 distinct populations with unique sensor offsets and speed values interact on the same trail grid, creating a complex, layered network topology with diverse branch widths and structures.
- **Orbiting Attractors**: 6 food sources move dynamically in a pulsing, circular orbit. The slime mold continually adapts, dissolving old trails and growing new ones to maintain connection with the moving food.

## Techniques

- **Vectorized Physarum Simulation**: 80,000 agents simulated in parallel using NumPy array calculations.
- **Heterogeneous Agent Properties**: Three agent species with different sensor angles, sensor distances, and step speeds:
  - **Species 0 (Teal)**: Sensor Angle = 22.5°, Sensor Distance = 12.0, Speed = 2.2
  - **Species 1 (Gold)**: Sensor Angle = 45.0°, Sensor Distance = 18.0, Speed = 1.6
  - **Species 2 (Magenta)**: Sensor Angle = 30.0°, Sensor Distance = 14.0, Speed = 2.8
- **NumPy Trail Diffusion**: Fast 3x3 box-blur using `np.roll` combinations and coordinate wrapping.
- **Volumetric Agent Bloom**: Pre-rendering agent densities into a separate 3-channel overlay, followed by a box-blur pass to create a soft, neon glow around individual firefly-like agents.
- **CIE/HSB Color Mapping**: A multi-stage RGB color lookup table mapping trail intensity values to a custom color gradient (Obsidian Void → Deep Forest Teal → Bioluminescent Mint → Solar Amber Gold).
- **Cinematic Camera Drift**: Eases a slow rotational wobble (`0.04 * sin(t)`) and camera zoom (`1.0 → 1.1`) over 20 seconds.

## Parameters

| Parameter | Value |
|---|---|
| Agents ($N$) | 80,000 |
| Grid size | 1280 × 720 |
| Pheromone deposit | 12.0 / step |
| Decay rate | 0.93 / frame |
| Food attractors | 6 (orbiting) |
| Output | 4K (3840 × 2160), 20s @ 60fps |

## Output

- `kinetic_physarum_slime_mold_network_2d.mp4` — 4K 60fps 20-second animation video
- `kinetic_physarum_slime_mold_network_2d_p1.png` — High-fidelity preview showing the self-organized loop network

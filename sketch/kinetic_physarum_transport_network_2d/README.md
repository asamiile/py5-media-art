# kinetic_physarum_transport_network_2d

An animated sequence of kinetic physarum transport network in 2D.

- **Theme**: A computational recreation of the Physarum polycephalum (slime mold) foraging behavior. Hundreds of thousands of microscopic autonomous agents navigate a void, leaving pheromone trails that diffuse and decay. The resulting emergent patterns form organic, interconnected transport networks resembling blood vessels, neural pathways, or cosmic webs.
- **Technique**: High-performance sensory-motor agent simulation (Physarum) using NumPy. 500,000 agents evaluate a scalar pheromone field at three sensor offsets (forward, left, right) to determine their steering angle. Agents advance and deposit pheromones. The environment field undergoes continuous $3 \times 3$ kernel diffusion and exponential decay. The pheromone density is mapped to an otherworldly, luminescent biological color palette.
- **Format**: Animation (15s @ 60fps)

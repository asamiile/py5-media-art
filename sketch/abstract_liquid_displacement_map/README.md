# abstract_liquid_displacement_map

A generative simulation of underwater light caustics and fluid refraction using displaced grid topologies.

- **Date**: 2026-05-23
- **Theme**: Fluid dynamics, water, optical refraction, caustics, bioluminescence, ocean currents.
- **Technique**: A dense 2D grid ($120 \times 80$) is mapped to a scrolling 3D Perlin noise field. Instead of using the noise to determine color or height directly, the script calculates the numerical derivative (gradient) of the noise field at each point. The $X$ and $Y$ coordinates of each grid point are then physically displaced by this gradient vector multiplied by a massive scalar ($8000$). This mathematically simulates optical refraction, where light rays bend based on the slope of a water wave. Additive blending (`py5.ADD`) naturally creates bright "caustic" bands where the displaced points bunch together. The entire field flows downwards over time, simulating a deep ocean current. 15s 60fps MP4.
- **Description**: Looking down into the depths of a bioluminescent ocean. Shimmering, fluid lines of light—known as caustics—dance and warp across the dark blue void. The light rays are bent and refracted by unseen, rolling waves, causing the grid to tear, overlap, and bunch together into intensely bright, neon-cyan ridges. The fluid motion is mesmerizing, flowing continuously downward like a digital waterfall of pure light.

# kinetic_chladni_plate_cymatics_2d

An autonomous generative physics simulation of Cymatics, visualizing the complex standing wave patterns (Chladni figures) formed on a vibrating metal plate.

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
The animation simulates 300,000 "sand" particles bouncing on a square plate. The physical vibration of the plate is mathematically modelled using the Chladni standing wave equation, where the amplitude $Z$ is a function of resonant modes $m$ and $n$.
By calculating the analytical gradient of $Z^2$, the simulation applies forces to the particles, driving them away from the antinodes (areas of maximum vibration) and causing them to settle at the nodal lines ($Z=0$, where the plate is stationary).
To make it kinetic, the resonant frequencies ($m, n$) are continuously modulated over time using sine waves. This forces the settled sand particles to frantically reorganize, sweeping across the plate to form entirely new geometric mandalas. The render uses speed-based coloring: fast-moving sand is drawn in dim, ghostly blue, while settled sand is drawn in brilliant, glowing gold, creating a strong contrast between chaos and structure.

# acoustic_levitation_drift

- **Theme**: Acoustic levitation, Gorkov potential, standing wave resonance, particle trapping.
- **Technique**: 3D Gorkov potential simulation. Particles are trapped in the nodes of a 3D standing wave field. The phase of the standing wave is slowly modulated, causing the trapped "beads" of light to drift and reorganize. Vectorized NumPy physics and P3D rendering.
- **Palette**: "Electric Cyan / Silver / Deep Emerald".
- **Description**: A dark void where thousands of silver and cyan specks are suspended in an invisible, vibrating grid. The grid slowly shifts and warps, carrying the specks in a rhythmic, coordinated dance that reveals the hidden geometry of sound.

## Technical Details

- **Simulation**: 15,000 particles trapped in a 3D standing wave potential $F \approx -\sin(k \cdot x + \phi)$.
- **Dynamics**: Particles are attracted to the nodes of the potential field with damping to simulate air resistance.
- **Modulation**: The phase of the X, Y, and Z waves is modulated using low-frequency oscillators, creating a dynamic, drifting lattice.
- **Rendering**: P3D additive point rendering with rotating camera.
- **Output**: 4K/60fps MP4.

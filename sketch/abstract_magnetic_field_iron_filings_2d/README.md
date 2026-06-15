# abstract_magnetic_field_iron_filings_2d

An animated 20s sequence simulating iron filings aligning to moving magnetic fields using thousands of tiny glowing particles.

## Theme
Simulating iron filings aligning to moving magnetic fields using thousands of tiny particles.

## Technique
A dense grid of 9,600 small line segments (filings) is drawn across the screen. Three invisible "magnets" (two attractors and one repulsor) orbit the screen using sine/cosine waves over time. For each filing, the vector forces from all magnets are calculated and summed to determine the angle and magnitude of the magnetic field at that point. The filings are rotated to align with the field, with their length and color mapping to the field's strength. Glowing tips and additive blending give it an electric, futuristic look.

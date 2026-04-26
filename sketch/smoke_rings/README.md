# smoke_rings

**Theme**: "Vortex ballet" — three smoke ring cross-sections rendered via fluid dynamics; each ring is a pair of counter-rotating point vortices whose Biot-Savart velocity field guides 50k tracer particles through the toroidal roll.

**Technique**: Point vortex simulation (Biot-Savart law), vectorized numpy integration, per-ring colored density accumulation via `np.bincount` weighting, log-scale tone mapping; three rings (cerulean · gold · mint) arranged across a wide canvas.

**Description**: Each smoke ring appears as two paired vortex cores in cross-section; 50k particles per ring are seeded as Gaussian clouds around each core and traced for 200 time steps under all six vortices' mutual induction. Density accumulation with log-scale mapping reveals the tight swirling cores and the diffuse return-flow halos — the characteristic anatomy of a toroidal vortex against near-black.

**Palette**:
- Background: `#06050c` near-black
- Left ring: cerulean `#3791f5`
- Center ring: gold `#f5c32d`
- Right ring: mint `#2de69b`

**Preview**: `preview.png`

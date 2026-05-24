# abstract_vector_field_magnetic_dipole

A physics-based generative simulation of 30,000 particles tracing the magnetic flux lines of moving dipoles.

- **Date**: 2026-05-23
- **Theme**: Magnetism, physics, vector fields, iron filings, electromagnetism, flux lines.
- **Technique**: Employs a fully NumPy-vectorized physics engine to update 30,000 particles at 60fps. The vector field is mathematically defined by four magnetic "poles" (positive and negative charges) that orbit each other in Lissajous curves. The force acting on each particle is calculated using Coulomb's/magnetic inverse-square law ($F \propto 1/r^2$). To simulate the visual look of iron filings aligning to a magnetic field, particles are drawn as short, additive-blended line segments (`py5.line` from old position to new position) over a motion-blur background. The color of the particles shifts from deep blue to bright cyan/white depending on their kinetic velocity. 15s 60fps MP4.
- **Description**: Like iron filings scattered over invisible magnets, tens of thousands of glowing particles align themselves into intricate, looping magnetic flux lines. The invisible poles dance and spin around each other, causing the magnetic field to warp and tear. The particles are continuously swept up in these invisible currents, creating breathtaking loops and figure-eights of glowing plasma that accelerate violently when trapped between opposing charges.

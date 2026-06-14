# fluid_perlin_vector_field_iridescence_2d

An animated 15s sequence showing 50,000 microscopic glowing particles swirling into turbulent, iridescent rivers over a black abyss.

## Theme
Millions of micro-particles flowing through a turbulent, invisible 2D vector field driven by multi-layered noise, leaving glowing, iridescent hair-like trails.

## Technique
A high-density 2D particle simulation running entirely on vectorized Numpy arrays for speed. Particle velocities are derived from a 3D OpenSimplex noise field. The background is minimally cleared each frame with a highly transparent black to create long, overlapping motion blur trails. Colors shift through a holographic spectrum based on particle angles.

# cybernetic_lorenz_attractor_swarm_3d

An animated 20s sequence of a 3D swarm of particles tracing a Lorenz strange attractor, leaving glowing neon blue and hot pink trails that fade out over time, creating a cybernetic butterfly wing shape.

## Theme
A 3D swarm of particles tracing a Lorenz strange attractor, leaving glowing trails.

## Technique
3D coordinates calculated iteratively using the Lorenz system differential equations. Particle histories are stored and drawn as lines using `py5.begin_shape() / py5.vertex() / py5.end_shape()` with glowing additive blending and fading alpha. The camera slowly orbits around the attractor to showcase its complex 3D shape.

# microscopic_amoeba_predator_prey_2d

An animated 20s sequence of a high-density microscopic ecosystem with a fluid dark background.

## Theme
A microscopic ecosystem where hundreds of glowing teal "amoeba" particles gently pulse in a fluid flowfield, while a few large deep-crimson "predator" cells chase them. When they collide, sparks burst out and the ecosystem continues to evolve.

## Technique
2D agent-based simulation. The predators use an attraction force towards nearby prey. Movement paths are disturbed by a global Perlin noise flowfield simulating a liquid slide. Additive blending with organic curves for the cells, drawn using `py5.curve_vertex` with dynamic noise to simulate organic wobble.

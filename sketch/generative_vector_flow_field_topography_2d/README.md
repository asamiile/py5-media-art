# generative_vector_flow_field_topography_2d

**Date**: 2026-07-07
**Type**: Animation (10-30s @ 60fps)

## Concept
A generative simulation of a dense vector flow field acting as topographical contours. 25,000 particles are dropped into a continuously evolving Perlin noise field. They trace the invisible currents, drawing smooth, sweeping curves that resemble fluid dynamics, topographical maps, or complex magnetic field lines.

## Techniques
The vector field is driven by `py5.os_noise` in 3D space (x, y, time). Every frame, particles update their heading based on the noise angle and move forward. The topography effect is achieved by softly fading the background with a low-opacity `py5.rect()`, allowing the particles to leave beautiful, semi-permanent glowing trails. Particles that drift off-screen are seamlessly respawned at random coordinates.

## Palette
Deep sea bioluminescence. The canvas is a dark abyssal blue. The particles emit a vibrant glow in deep sea teals, bright cyans, and emerald greens, creating a serene, fluid atmosphere.

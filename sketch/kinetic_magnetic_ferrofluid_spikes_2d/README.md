# kinetic_magnetic_ferrofluid_spikes_2d

## Concept
A simulation of magnetic ferrofluid reacting to dynamic, pulsating magnetic poles. The fluid is drawn toward invisible attractors while swirling through an organic flow field, rendering as thick, glossy black spikes that emerge and dissolve on a clean metallic surface.

## Technique
A particle simulation (8,000 particles) using `numpy` for vectorized physics. Particles are driven by a combination of weak geometric attractors (poles following Lissajous curves) and a trigonometric 2D flow field to spread them out. They are drawn using `py5.vertices()` where each particle forms a spiky line segment matching its velocity vector, creating the signature ferrofluid spikiness. Subtractive trailing (`py5.rect` with low opacity) creates a smooth fading effect.

## Format
Animation (15s @ 60fps)

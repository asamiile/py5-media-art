# kinetic_chromatic_aberration_vortex_2d

An abstract procedural animation depicting a swirling vortex of geometric shapes getting pulled into a massive gravitational singularity. As the entities spiral inward toward the center, intense chromatic aberration causes their RGB light waves to separate and distort, producing intense glowing trails and color-banding before they cross the event horizon.

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
To render this in real-time, the sketch utilizes 15,000 independent moving vertices managed natively in NumPy. Rather than using slow individual `rect()` calls, it computes the exact rotation and coordinates for thousands of quads using a vectorized rotation matrix, and pushes them to the Py5 canvas simultaneously using `py5.QUADS`. 

To create the chromatic aberration effect, the system draws three complete passes over the particles (Red, Green, Blue). The radial position and rotational angle of each particle are displaced mathematically by an amount inversely proportional to their distance from the center hole ($D = k/r$), simulating the bending of light. Additive blending recombines the separated layers into pure white near the edges and vivid neon separations near the center.

# kinetic_physics_double_pendulum_swarm_2d

A kinetic simulation visualizing the chaotic nature of classical physics through a swarm of 200,000 double pendulums.

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
The double pendulum is a classic example of deterministic chaos—a system where minuscule differences in initial conditions lead to wildly divergent outcomes. This sketch simulates 200,000 independent double pendulums simultaneously using highly vectorized NumPy operations. Every pendulum starts in an identical horizontal position, but with a microscopic random variation ($10^{-6}$ radians) in their initial angle. 
Over the 15-second animation, the pendulums swing as a single solid stroke of light, until the chaos takes over. The stroke slowly splits into ribbons, which then shatter into a massive, fluid-like swarm of glowing dust tracing complex orbital paths. The points are colored based on their velocity (Cyan for fast, Purple for mid, Magenta for slow) and drawn with additive blending and motion blur.

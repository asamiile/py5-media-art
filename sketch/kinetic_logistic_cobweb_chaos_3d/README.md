# kinetic_logistic_cobweb_chaos_3d

![Preview](kinetic_logistic_cobweb_chaos_3d_p1.png)

## Metadata
- **Date**: 2026-08-02
- **Theme**: The period-doubling route to chaos in the logistic map.
- **Technique**: Logistic map iteration, cylindrical 3D coordinate mapping, custom 3D rotations, painters depth sorting, and vectorized multi-pass stroke glow.
- **Logic Lab Reference**: `chaos_theory/logistic_map/logistic_map.py`

## Concept
This sketch explores the visual evolution of a simple nonlinear dynamical system: the logistic map, governed by the recurrence relation $x_{n+1} = r \cdot x_n \cdot (1 - x_n)$. Rather than a traditional flat diagram, the 2D cobweb coordinate staircase of 250 independent trajectories is projected onto a 3D cylinder. The parameter $r$ is continuously modulated over the 15-second loop: starting at $r=2.9$ (stable period-1 fixed point), it sweeps through period-doubling bifurcations ($r=3.2$, $r=3.5$) into strong chaos ($r=3.99$), and back. This results in a physical unfolding and dispersion of a single glowing cyan coordinate ring into a multi-stranded, shimmering helical cage of purple, violet, and gold threads before synchronizing back into unity.

## Technical Details
- **Renderer**: P2D
- **Simulation**: Vectorized computation of 250 trajectories running 2 steps per frame, keeping a sliding history window of 120 points (60 steps).
- **Visuals**: Cylindrical coordinate projection, manual Y and Z rotations, painters algorithm depth sorting, 10 depth-bins per color group, depth-cueing scale/opacity modifiers, and a background starfield.
- **Animation**: 15 seconds (900 frames) @ 60 FPS.

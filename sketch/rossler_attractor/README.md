# rossler_attractor

**Theme**: "Spiral descent" — the Rössler attractor; a 3D chaotic system whose orbits wind outward in the (x,y) plane in a broad spiral before snapping back through a narrow fold at high z, then repeating — a fundamentally different shape from the Lorenz butterfly

**Technique**: Vectorised RK4 integration of 250 parallel trajectories (35k steps each); density split into three z-height layers (low/mid/high) each accumulated separately; additive colour compositing of violet (low z), teal (mid z), gold (high z) layers; log-scale tone mapping per layer

**Description**: The Rössler system (dx/dt = −y−z, dy/dt = x+ay, dz/dt = b+z(x−c), a=b=0.2, c=5.7) traces a wide clockwise spiral in the (x,y) plane. Near the outer edge, each orbit is pushed to high z values (the snap-back fold) before being injected back at low z near the centre. Z-height coloring makes this fold visible as a bright gold crescent at the top-right against the deep violet spiral body. The dark void at the centre is the attractor's characteristic hollow core.

**Palette**:
- Background: `#05040a` near-black
- Low z (spiral body): `#1c1264` deep violet
- Mid z (transition): `#087890` electric teal
- High z (snap-back fold): `#dcb41c` warm gold

**Preview**: `preview.png`

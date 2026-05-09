# Spectral Tesseract Unfolding

A 4D geometric simulation exploring higher-dimensional rotation and perspective projection.

## Concept

This artwork visualizes the rotation of a 4D hypercube (tesseract) through a dual-plane rotation ($xy$ and $zw$). By projecting this higher-dimensional object into 3D space, we witness the warping and "unfolding" of its structure, revealing geometric relationships that are invisible in our three-dimensional world.

## Technical Details

- **4D Sampling**: 200,000 particles sampled across the 8 cubic "faces" (cells) of a 4D hypercube.
- **Rotation**: Simultaneous rotation in the $xy$ and $zw$ planes using 4x4 rotation matrices.
- **Projection**: Perspective projection from 4D to 3D space, where the $w$ coordinate influences the 3D scale and iridescent color mapping.
- **Rendering**: Multi-pass additive point rendering with a spectral HSB shift (Indigo to Violet to Gold).
- **Environment**: 4K/60fps animation with a high-density background starfield.

## Aesthetics

The visual impression is one of mathematical precision and cosmic mystery. The iridescent "Spectral Indigo" core pulses with a golden aura as it turns, casting shimmering shadows across the star-dusted void. The complex self-intersection and warping of the Projected structure highlight the counter-intuitive nature of 4D geometry.

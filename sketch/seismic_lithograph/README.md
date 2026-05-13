# seismic_lithograph

A 10 second animation of low seismic pulses crossing an etched stone slab. Layered shale bands hold a dim memory of stress while diagonal faults heat into rust and sulfur for a few frames, then sink back into mineral darkness.

## Technique

- 2D finite-difference wave field with layer-dependent stiffness.
- Fault masks add nonlinear slip and localized heat memory.
- Vectorized NumPy buffers are rendered into py5 pixels and encoded as a 4K/60fps MP4.

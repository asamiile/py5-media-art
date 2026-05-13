# chromatophore_signal_skin

10-second 4K/60fps py5 animation of cephalopod-like chromatophores expanding and contracting across living skin as pale neural waves travel through the tissue.

The renderer uses a staggered procedural cell lattice, vectorized radial pigment masks, iridescent inner rings, and a fading signal-memory buffer. Frames are written through py5's pixel array, encoded with FFmpeg as `output.mp4`, mirrored to `chromatophore_signal_skin.mp4`, and sampled at mid-frame for `chromatophore_signal_skin_p1.png`.

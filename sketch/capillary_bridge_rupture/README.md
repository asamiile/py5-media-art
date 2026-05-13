# capillary_bridge_rupture

A 10 second animation of microscopic droplets forming unstable capillary bridges. Thin liquid necks stretch between neighboring drops, flash amber as they rupture, and leave faint residue rings on a dark brushed substrate.

## Technique

- Metaball droplet field with animated centers and radii.
- Segment-distance capillary bridges between near neighbors.
- Neck-thinning rupture events accumulate into a fading residue buffer.
- Encoded with FFmpeg as `output.mp4` and mirrored to `capillary_bridge_rupture.mp4`.

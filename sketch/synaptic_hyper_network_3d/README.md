# synaptic_hyper_network_3d

## Details
- **Date**: 2026-06-03
- **Format**: Animation (15s @ 60fps)
- **Theme**: A vast, complex 3D network of glowing synapses and pulsing neurons, dynamically routing light packets across interconnected nodes.
- **Technique**: Procedurally generated 3D network using `scipy.spatial.Delaunay` within a sphere. Edges are filtered by length to ensure localized connections. Pulses of light travel along the lines (synapses) driven by a time-varying noise function, and nodes pulse when stimulated. Additive blending is used for the synapses.
- **Color palette**:
  - Background: Pitch Black
  - Dominant (60%): Electric Blue
  - Secondary (30%): Deep Purple
  - Accent (10%): Hot Magenta (active synapses)
  - Mood: biological / cybernetic

## Description
An animated 3D simulation of a complex neural or cybernetic network. Thousands of connections between nodes form a spherical web. As time progresses, waves of activity (driven by 3D noise) sweep through the network, causing individual synapses to flare hot magenta and connected nodes to glow brightly before fading back to a deep electric blue baseline state.

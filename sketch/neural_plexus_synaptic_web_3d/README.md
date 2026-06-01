# neural_plexus_synaptic_web_3d

## Theme
A dense biological/cybernetic "Plexus" particle system in 3D space. Nodes drift elegantly like neurons forming and breaking synaptic connections as data flows through a massive network.

## Technique
Generating 300 nodes drifting in 3D space. Their coordinates are governed by a continuous 3D OpenSimplex noise field traversing a circle in time, guaranteeing a seamless 10-second loop. A highly optimized, vectorized Numpy array dynamically calculates all 90,000 pairwise distances per frame. When nodes float within a specific proximity threshold, glowing geometric lines are drawn between them, with opacity fading out based on the inverse distance squared.

## Color palette
- Background: Deep teal/navy
- Dominant: Bioluminescent green
- Secondary: Electric cyan
- Mood: Sci-Fi / Biological / Data

## Format
Animation (10s @ 60fps)

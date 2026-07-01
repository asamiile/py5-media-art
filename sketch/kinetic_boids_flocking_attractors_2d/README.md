# kinetic_boids_flocking_attractors_2d

## Concept
Craig Reynolds' classic "Boids" artificial life algorithm. This algorithm simulates the emergent flocking behavior of birds or schools of fish based on three simple rules: Separation, Alignment, and Cohesion. When applied to 3,000 interacting particles simultaneously, they form beautiful, fluid, self-organizing streams and chaotic schooling patterns.

## Technique
Evaluating the 3 rules for 3,000 birds means calculating 9,000,000 pairwise distances per step. By vectorizing the entire algorithm using `scipy.spatial.distance.cdist` and heavy NumPy array broadcasting, I'm able to run the simulation extremely quickly. I also added an invisible global attractor in the center to gently pull the flocks back onto the screen so they don't wander off.

## Palette
- **Base**: Fading dark background
- **Boids**: Buckets of glowing Red, Green, and Blue trails
- **Mood**: Electric, fluid, swarming, chaotic, alive

## Format
Animation (450 frames @ 30fps)

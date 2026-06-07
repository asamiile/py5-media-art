# Algorithmic Crystal Growth Fractal 3D

## Concept
A 3D simulation of a massive, glowing, branching crystal structure that grows outward procedurally using recursive L-systems, rendered with sharp, angular metallic/glassy pyramids and octahedrons.

## Technique
* Recursive L-system branching algorithm in 3D
* Organic morphing of angle and scale using time-based trigonometric functions
* Additive blending with deep color hues mapped by recursive depth
* Directional and ambient lighting for sharp glass-like reflections

## Palette
* Deep spectrum generated randomly at runtime combined with depth-based HSB adjustments
* Additive blending (`py5.ADD`)

## Specifications
- Resolution: 3840x2160
- Frame Rate: 60 FPS
- Duration: 15s (900 Frames)
- Architecture: Python `py5` with recursive pushing/popping of matrix state

## Notes
The recursive depth is capped at 6 with variable branches to maintain 60FPS while rendering thousands of interconnected geometry boxes mimicking crystal shards.

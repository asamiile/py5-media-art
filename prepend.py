import os

works_content = """## generative_boids_flocking_simulation_2d

- **Date**: 2026-06-26
- **Theme**: A simulation of avian murmuration, where hundreds of digital entities flock and weave across the canvas, guided by shifting invisible currents.
- **Technique**: Uses a modified boids steering behavior algorithm optimized for Python execution speed. Rather than O(N^2) pairwise distance checks for alignment and cohesion, the boids are steered by a globally continuous 3D OpenSimplex noise field that mimics macroscopic group flow. The boids are drawn as oriented triangles that leave semi-transparent trails as they move.
- **Description**: An animated 15s sequence of digital boids flocking through a noise field.

"""

feedback_content = """## generative_boids_flocking_simulation_2d

- **Rating**: 
- **Comment**: 

"""

def prepend_to_file(filepath, content_to_prepend):
    with open(filepath, "r") as f:
        content = f.read()
    with open(filepath, "w") as f:
        f.write(content_to_prepend + content)

prepend_to_file("sketch/WORKS.md", works_content)
prepend_to_file(".agents/FEEDBACK.md", feedback_content)

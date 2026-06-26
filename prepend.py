import os

works_content = """## generative_cyberpunk_neon_rain_matrix_2d

- **Date**: 2026-06-26
- **Theme**: A stylized, glitching digital rain sequence inspired by cyberpunk aesthetics and the classic Matrix digital rain, replaced with abstract glowing geometric segments.
- **Technique**: Uses thousands of independent dropping particles with simulated depth (z-index) determining their size, speed, and brightness. High-frequency OpenSimplex noise is sampled as the drops fall to trigger sudden horizontal glitch displacements and color inversions, adding a dynamic, corrupted digital feel. Rendered in a 2D context using semi-transparent background clearing for motion trails.
- **Description**: An animated 15s sequence of digital neon rain with glitch effects.

"""

feedback_content = """## generative_cyberpunk_neon_rain_matrix_2d

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

import os

works_content = """## generative_isometric_labyrinth_2d

- **Date**: 2026-06-26
- **Theme**: A shifting, Escher-like maze of isometric columns that rise and fall based on 3D noise patterns.
- **Technique**: Uses standard 2D vector drawing to simulate a 3D isometric projection, completely bypassing OpenGL/P3D engine. Sorts blocks back-to-front based on grid iteration. Color and column height are driven by OpenSimplex noise parameterized by time.
- **Description**: An animated 15s sequence of an isometric labyrinth continuously shifting.

"""

feedback_content = """## generative_isometric_labyrinth_2d

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

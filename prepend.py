import os

works_content = """## generative_optical_illusion_truchet_tiles_2d

- **Date**: 2026-06-26
- **Theme**: A mesmerizing grid of flowing lines that constantly shift, connect, and disconnect, creating optical illusions of labyrinthine paths.
- **Technique**: Utilizes a classic Truchet tiling system where each cell contains two diagonal arcs. However, instead of being statically randomized, the rotation of each tile is mapped to a 3D OpenSimplex noise field moving through time. This causes the tiles to smoothly animate between 90-degree orientations, continually redrawing the maze in an undulating wave of glowing colors.
- **Description**: An animated 15s sequence of dynamic Truchet tiles.

"""

feedback_content = """## generative_optical_illusion_truchet_tiles_2d

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

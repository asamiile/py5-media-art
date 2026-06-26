import os

works_content = """## kinetic_magnetic_compass_array_2d

- **Date**: 2026-06-26
- **Theme**: A vast 2D array of tiny magnetic compass needles, reacting to unseen magnetic currents passing underneath them.
- **Technique**: 2D point grid where each point represents the anchor of a compass needle. A 3D noise vector field determines the angle of the compasses, creating sweeping, colorful waves across the grid.
- **Description**: An animated 15s sequence of kinetic magnetic compass needles.

"""

feedback_content = """## kinetic_magnetic_compass_array_2d

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

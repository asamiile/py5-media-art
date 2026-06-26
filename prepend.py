import os

works_content = """## generative_recursive_tree_canopy_2d

- **Date**: 2026-06-26
- **Theme**: A forest canopy of abstract, recursive geometric trees that sway continuously in an invisible, mathematically generated wind.
- **Technique**: Uses a recursive fractal branching algorithm to generate tree structures. The angle of each branch varies dynamically using continuous OpenSimplex noise and trigonometric functions, simulating organic growth and environmental wind forces. Colored glowing circles represent leaves blooming at the tips of the branches.
- **Description**: An animated 15s sequence of recursive swaying fractal trees.

"""

feedback_content = """## generative_recursive_tree_canopy_2d

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

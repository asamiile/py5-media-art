import os

works_content = """## abstract_geometric_kaleidoscope_fractal_2d

- **Date**: 2026-06-26
- **Theme**: A glowing, infinitely unfolding geometric fractal that mimics the shifting mirrors of a kaleidoscope.
- **Technique**: Uses standard 2D recursive rendering. At each level of recursion, the shape splits into 6 branches that rotate and translate based on time and their recursive depth. The ADD blend mode creates intense glowing intersections where the semi-transparent layers overlap.
- **Description**: An animated 15s sequence of a geometric fractal kaleidoscope unfolding.

"""

feedback_content = """## abstract_geometric_kaleidoscope_fractal_2d

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

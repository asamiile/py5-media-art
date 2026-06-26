import os

works_content = """## generative_flow_field_topography_2d

- **Date**: 2026-06-26
- **Theme**: A continuous generation of contour-like lines flowing across the screen, mimicking the look of dynamically shifting topographical maps.
- **Technique**: Uses thousands of individual particles navigating through a time-varying OpenSimplex noise vector field. A semi-transparent background clearing technique is used to create smooth, lingering trails that fade over time.
- **Description**: An animated 15s sequence of topographic flow fields evolving dynamically.

"""

feedback_content = """## generative_flow_field_topography_2d

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

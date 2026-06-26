import os

works_content = """## generative_wavy_sine_landscapes_2d

- **Date**: 2026-06-26
- **Theme**: A scrolling, atmospheric 2D landscape of undulating mountains and waves, featuring a vibrant retro-synthwave color palette.
- **Technique**: Renders 25 layered polygon shapes drawn back-to-front. The vertices of each layer are modulated by a combination of OpenSimplex noise and sine waves, creating organic, rolling terrain. A parallax scrolling effect is achieved by increasing the horizontal offset speed for layers closer to the foreground. Colors are algorithmically shifted based on time and depth, creating a dynamic, atmospheric haze.
- **Description**: An animated 15s sequence of a scrolling layered mountain landscape.

"""

feedback_content = """## generative_wavy_sine_landscapes_2d

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

import os

works_content = """## abstract_geometric_spirograph_mandala_2d

- **Date**: 2026-06-26
- **Theme**: A glowing, hypnotic digital spirograph that traces complex mandala patterns over time.
- **Technique**: Uses compounded trigonometric functions (sine and cosine waves with differing frequencies and amplitudes) to calculate the paths of 12 distinct points. As the animation progresses, these points trace out intricate, overlapping geometric motifs on a non-clearing background. The `ADD` blend mode ensures that overlapping strokes build up intensely bright, glowing intersections, mimicking long-exposure light painting.
- **Description**: An animated 15s sequence tracing out a glowing spirograph mandala.

"""

feedback_content = """## abstract_geometric_spirograph_mandala_2d

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

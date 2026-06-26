import os

works_content = """## kinetic_chladni_plate_resonance_2d

- **Date**: 2026-06-26
- **Theme**: A visualization of Chladni figures, simulating sand particles organizing themselves into intricate, shifting geometric patterns driven by unseen acoustic vibrations.
- **Technique**: 2D particle system physics simulation. A mathematical standing wave equation determines the nodal lines across the surface. Particles are pushed down the gradient of the amplitude towards the nodes.
- **Description**: An animated 15s sequence of kinetic sand particles resonating on a plate.

"""

feedback_content = """## kinetic_chladni_plate_resonance_2d

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

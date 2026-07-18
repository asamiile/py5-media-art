import os

def prepend(file_path, text, header_lines=0):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    with open(file_path, 'w') as f:
        for i in range(header_lines):
            f.write(lines[i])
        f.write(text + "\n\n")
        for i in range(header_lines, len(lines)):
            f.write(lines[i])

works_text = """## kinetic_generative_vector_field_flow_2d
- **Date**: 2026-07-08
- **Type**: Animation (900 frames, 60fps)
- **Concept**: A flowing, organic visualization of a mathematical vector field driven by high-dimensional Perlin noise, creating the illusion of wind or fluid currents.
- **Techniques**: 20,000 independent particles trace paths through a continuous vector field. To achieve a perfect seamless loop over the 15-second duration, the vector field is generated using 4D Perlin noise, where the 3rd and 4th dimensions trace a perfect circle (using Cosine and Sine of the time variable). Particles have a short lifespan and are drawn with fading trails using additive blending.
- **Palette**: A dark, warm indigo background with millions of overlapping semi-transparent trails glowing in a sweeping rainbow gradient based on their screen position and time."""

feedback_text = """## kinetic_generative_vector_field_flow_2d

- **Rating**: 
- **Comment**: """

prepend('sketch/WORKS.md', works_text, 0)
prepend('.agents/FEEDBACK.md', feedback_text, 6)

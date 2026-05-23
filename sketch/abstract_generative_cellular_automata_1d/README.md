# abstract_generative_cellular_automata_1d

A 3D isometric visualization of Stephen Wolfram's Rule 30 Elementary Cellular Automaton as a kinetic digital tapestry.

- **Date**: 2026-05-23
- **Theme**: Cellular automata, Rule 30, chaos theory, weaving, digital tapestry, isometric projection.
- **Technique**: Implements a 1D elementary cellular automaton using Rule 30, famous for generating complex, pseudo-random, chaotic patterns from a single starting pixel. Instead of rendering it as a static 2D image, the automaton is rendered as a scrolling $100 \times 100$ grid of 3D cubes (`py5.box`) using an isometric camera projection. Every 3 frames, a new row is calculated at the top and the entire history shifts downward, creating a cascading waterfall effect. The "active" (`1`) states are rendered as tall, emissive gold pillars, while the "inactive" (`0`) states are short, dark obsidian blocks. A secondary sine wave ripple distorts the Z-axis of the entire tapestry. 15s 60fps MP4.
- **Description**: A breathtaking digital tapestry weaves itself in real-time. Rendered in a deep, moody isometric 3D view, a chaotic but highly structured pattern cascades downward like a waterfall. The pattern is built from thousands of individual geometric blocks—glowing, metallic gold pillars representing "alive" cells, and dark obsidian blocks representing "dead" cells. The chaotic geometry of Rule 30 creates striking triangle patterns that slide gracefully across the screen as the entire woven structure slowly rotates in three-dimensional space.

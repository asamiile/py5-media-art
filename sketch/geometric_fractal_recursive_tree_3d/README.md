# geometric_fractal_recursive_tree_3d

A kinetic 3D fractal tree generated via recursive L-system logic.

- **Date**: 2026-05-23
- **Theme**: Fractals, recursive trees, L-systems, algorithmic botany, nature, wind simulation.
- **Technique**: Uses a pure recursive function (`draw_branch`) to draw a highly complex 3D tree. The function draws a line (the branch trunk), translates to its tip, and then calls itself 3 times. Each child branch is rotated evenly around the Y-axis (creating a volumetric canopy) and tilted outwards. The recursion depth is 9, resulting in $3^9$ (nearly 20,000) individual branch segments. Global time `t` continuously modulates the branching angles and applies Perlin noise-based wind sway. The hue shifts dynamically based on recursion depth. 15s 60fps MP4.
- **Description**: A magical, glowing digital tree grows upward from the bottom of the screen into a dense, sprawling canopy. The tree is composed of thousands of glowing neon lines that shift from deep indigo at the thick trunk to vibrant cyan and green at the delicate outer branches. The entire tree is constantly in motion—not only rotating slowly in 3D space, but each branch gracefully swaying and curling inward and outward as if caught in an ethereal, shifting wind.

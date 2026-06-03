# Geometric Tesseract 4D Rotation

## Description
A 4D hypercube (tesseract) slowly rotating and casting a 3D shadow into our reality, its vertices connected by glowing energy beams that pulse as they cross dimensional planes. The animation explores higher-dimensional geometry and stereographic projection in generative art.

## Technical Details
- **Format:** Animation (10s @ 60fps)
- **Palette:** Dark void background with electric cyan edges and bright white pulsing spherical vertices.
- **Algorithm:** 4D to 3D projection math. 16 vertices of a tesseract in 4D space are multiplied by 4D rotation matrices (using combinations of XW, YW, ZW planes) and then projected down to 3D using perspective projection.
- **Renderer:** py5.P3D with HSB depth-based color sorting and custom matrix transformations.

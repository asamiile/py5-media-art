# kinetic_geometric_tesseract_rotation_4d

Projecting a 4D hypercube (Tesseract) into 3D, and then into 2D. We rotate it in 4D space across the XW and YZ planes, generating a shape that continuously turns itself inside out.

## Techniques

16 vertices connected by 32 edges. Manual 4D rotation matrices, followed by a stereographic projection into 3D, then perspective into 2D. Drawn with 40 nested tesseracts with slightly offset rotation phases.

## Palette

Wireframe matrix-green/cyan with additive blending.

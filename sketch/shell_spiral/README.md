# shell_spiral

**Theme**: "Growth spiral" — a nautilus shell cross-section; biological growth encoded in the logarithmic spiral where each whorl is a scaled replica of the last

**Technique**: Moseley's logarithmic spiral model (r = r₀·eᵇᶿ), chamber segmentation via equal-angle septa, radial shading by whorl age

**Description**: The shell tube follows r = r₀·exp(b·θ) with growth rate b=0.18, producing 4.5 complete whorls fitting the canvas. The tube has inner and outer boundaries at ratio TUBE_RATIO=0.85, giving the shell wall its thickness. 32 chambers are delimited by septa — radial lines at equal angular intervals. Each chamber is shaded by its whorl index (outer = ivory-cream, inner = darker ochre) to suggest depth and age. A dark columella anchors the center. The self-similar geometry means every segment is geometrically identical to every other at a different scale.

**Palette**:
- Background: `#100c08` warm near-black
- Outer whorl: `#e8dec4` ivory cream
- Inner whorls: `#b49664` warm ochre
- Septa / outline: `#50361e` dark brown
- Columella: `#28180c` deep shadow

**Preview**: `preview.png`

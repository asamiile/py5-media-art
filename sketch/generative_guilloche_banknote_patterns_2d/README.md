# generative_guilloche_banknote_patterns_2d

An animated sequence of generative guilloche banknote patterns in 2D.

- **Theme**: A hypnotic, continuously evolving Guilloché pattern (banknote security pattern) formed by parametric equations of nested epitrochoids and hypotrochoids. The intricate webs of fine, glowing threads weave in and out of phase.
- **Technique**: A 2D sketch that draws overlapping parametric curves. The parameters for the radii and frequencies slowly shift using OpenSimplex noise. To get the classic banknote look, thousands of vertices are connected via begin_shape() and end_shape(). We use additive blending and thin strokes.
- **Format**: Animation (15s @ 60fps)

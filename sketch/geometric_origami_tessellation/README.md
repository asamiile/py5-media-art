# geometric_origami_tessellation

A real-time 3D simulation of geometric origami tessellations, inspired by the Miura-ori fold.

- **Date**: 2026-05-23
- **Theme**: Origami, paper folding, Miura fold, geometric tessellation, mathematical surfaces.
- **Technique**: Uses a dense 2D grid (`py5.QUAD_STRIP`) to simulate a massive sheet of paper. A base "fold angle" ($\theta$) oscillates via a sine wave, causing the entire paper to contract on the X-axis while simultaneously expanding on the Z-axis in an alternating, checkerboard pattern. This creates the classic "accordion" structure of rigid origami. To make it visually organic, the fold angle is modulated locally by 3D Perlin noise, causing the rigid geometric folds to ripple, warp, and crumple slightly like real, stiff iridescent paper. 15s 60fps MP4.
- **Description**: A vast, flat plane of iridescent material slowly begins to fold itself. Guided by invisible mathematical laws, the surface collapses inward, forming a highly complex, repeating geometric pattern of sharp ridges and deep valleys (a Miura-ori tessellation). Strong directional lights catch the shifting angles of the folds, revealing a spectrum of glowing cyan and magenta hues. As the structure slowly spins, the paper breathes—unfolding back into a nearly flat plane before deeply crumpling again in a mesmerizing, organic rhythm.

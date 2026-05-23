# recursive_fractal_spirograph

A fully 3D, recursive spirograph that draws a continuous, glowing neon ribbon through the void.

- **Date**: 2026-05-23
- **Theme**: Spirograph, hypotrochoid math, recursive geometry, 3D ribbons.
- **Technique**: Simulates a series of 4 nested, rotating linkages (similar to a robotic arm or planetary gears). Each linkage rotates on multiple axes (X, Y, and Z) at different speeds, creating a highly complex, chaotic 3D orbit for the final "pen" tip. The tip's position is recorded in a fixed-length memory queue (1500 points). To render the trail, a `py5.TRIANGLE_STRIP` is extruded along the path by calculating the tangent vector and expanding outward to create a flat "ribbon" that tapers and fades at the tail. The entire shape rotates in P3D, producing a mesmerizing, self-intersecting knot of glowing HSB colors. 15s 60fps MP4.
- **Description**: A brilliantly glowing ribbon of rainbow light dances wildly in the center of a black abyss. Like an invisible, multi-jointed pendulum swinging in all three dimensions, it draws an intricate, chaotic, yet perfectly mathematical knot. The glowing trail slowly fades into darkness at its tail, creating a beautiful long-exposure photography effect, as the entire 3D construct smoothly rotates before the viewer.

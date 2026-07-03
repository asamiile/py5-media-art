# kinetic_stained_glass_voronoi_2d

An animated sequence of kinetic stained glass voronoi in 2D.

- **Theme**: A living stained glass window. 1,200 autonomous cells continuously shift and jostle, generating a flawless Voronoi tessellation. The cellular boundaries flex and morph as if breathing, while the interior of each cell shimmers with an iridescent, jewel-toned gradient that responds to the fluid motion.
- **Technique**: High-performance geometric tessellation using `scipy.spatial.Voronoi`. 1,200 dynamic seed points move according to a subtle fluid flow field (Perlin/Simplex noise) to avoid chaotic bouncing. Each frame, the Voronoi regions are computed and rendered as filled polygons. To handle boundaries cleanly, static anchor points are placed far outside the canvas. Colors are sampled from a slow-moving, multi-dimensional noise space based on the centroid of each cell.
- **Format**: Animation (15s @ 60fps)

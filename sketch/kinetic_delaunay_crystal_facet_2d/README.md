# kinetic_delaunay_crystal_facet_2d

An animated sequence of kinetic delaunay crystal facet in 2D.

- **Theme**: A living crystal structure formed by dynamic Delaunay triangulation. A constellation of autonomous nodes continuously reorganizes itself, creating a faceted, low-poly surface that shimmers and shifts like a liquid gemstone.
- **Technique**: High-performance geometric graph rendering using `scipy.spatial.Delaunay`. 1,500 autonomous particles drift through a 2D space, governed by simple kinetic physics (velocity, boundary reflection). Each frame, the nodes are triangulated to form a contiguous mesh. The fill color of each triangle is determined by the spatial position of its centroid, mapping to an iridescent gradient.
- **Format**: Animation (15s @ 60fps)

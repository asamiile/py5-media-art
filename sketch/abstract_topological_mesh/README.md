# abstract_topological_mesh

A glossy, morphing 3D topological mesh based on mathematical surface functions.

- **Date**: 2026-05-23
- **Theme**: Topology, non-Euclidean geometry, mathematical surfaces, abstract mesh.
- **Technique**: Uses NumPy's `meshgrid` to highly optimize the calculation of a 10,000-vertex grid ($100 \times 100$). The $Z$-height of each vertex is governed by a dynamic mathematical equation that combines a hyperbolic paraboloid (saddle shape) with time-varying 3D sine and cosine ripples. The mesh is rendered using `py5.TRIANGLE_STRIP` for performance. A strong specular highlight (`py5.specular`, `py5.shininess`) and directional lighting are applied, giving the abstract math surface the appearance of glossy, wet liquid or polished plastic. The color of the mesh maps smoothly to its vertical displacement, shifting over time. 15s 60fps MP4.
- **Description**: A vast, glossy landscape of geometric ripples morphs fluidly in a dark void. The surface bends into a massive, saddle-like shape, while high-frequency ripples wash across it like waves in a thick alien liquid. The mesh shines with intense specular highlights under a bright artificial light. As the landscape slowly spins, its colors shift organically through a spectrum of oceanic cyans, deep blues, and vibrant neon pinks, perfectly matching the peaks and valleys of its mathematical topology.

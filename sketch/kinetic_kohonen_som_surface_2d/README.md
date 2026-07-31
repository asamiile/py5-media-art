# kinetic_kohonen_som_surface_2d

**Date**: 2026-07-31  
**Type**: Animation (1200 frames, 60fps)  

## Concept

A 4K kinetic visualization of a **Kohonen Self-Organizing Map (SOM)** neural sheet unfolding and wrapping itself around a 3D Torus Knot manifold. A $35 \times 35$ grid of neurons starts as a flat sheet and learns in an unsupervised competitive manner, adapting to training signals sampled along the surface of a torus knot in 3D space. The 3D lattice rotates continuously, projected onto a 2D screen with depth shading and organic pulsing bloom. The result is a shimmering holographic mesh that twists and wraps itself around an invisible 3D sculpture, combining neural topology learning with cosmic geometry.

## Techniques

- **Kohonen Self-Organizing Map competitive learning**:
  The neuron grid learns a mapping of a 3D manifold. For each input signal $S \in \mathbb{R}^3$, the best matching unit (BMU) is identified. The weights of the BMU and its grid neighbors are updated:
  $$\Delta W_i = \eta(t) \cdot h(i, \text{BMU}, t) \cdot (S - W_i)$$
  where $\eta(t)$ is the exponentially decaying learning rate and $h(i, \text{BMU}, t)$ is the Gaussian neighborhood influence which shrinks over time.

- **Knot-Manifold Sampling**:
  Training signals are drawn dynamically from a $(3, 7)$ torus knot equation with Gaussian noise thickness, creating a solid tube shape for the SOM to wrap around:
  $$r = 0.22 \cdot (2.0 + \sin(7 \theta))$$
  $$x = 0.5 + r \cdot \cos(3 \theta)$$
  $$y = 0.5 + r \cdot \sin(3 \theta)$$
  $$z = 0.5 + 0.22 \cdot \cos(7 \theta)$$

- **Manual 3D Rotation and Perspective Projection**:
  To ensure stability and cross-platform consistency, rotated 3D coordinates are calculated manually via trigonometric transform matrices. These coordinates are projected orthographically to the 2D canvas with custom scaling.

- **Depth Shading and Concentric Bloom**:
  Line weights, node sizes, and alphas are modulated based on the rotated Z (depth) coordinate. Vertices in the foreground glow in high-alpha Radiant Magenta (`#ff2a85`), while background elements transition into thin, low-alpha Glacial Cyan (`#00e5ff`) edges, emphasizing the three-dimensional form. A Perlin noise loop generates organic twinkling on the network nodes.

- **Persistent Motion trails**:
  A trail decay overlay (`alpha = 18` out of 255) keeps a fading history of prior states, resulting in visual smoothing of the rotation.

## Palette

- **Background**: Obsidian Void (`#040508`).
- **Foreground (Closer Nodes/Edges)**: Radiant Magenta (`#ff2a85`).
- **Mid-ground (Structural lattice)**: Electric Violet (`#b356ff`).
- **Background (Distant Nodes/Edges)**: Glacial Cyan (`#00e5ff`).

# kinetic_iridescent_metaballs_2d

An animated sequence of kinetic iridescent metaballs in 2D.

- **Theme**: A mesmerizing simulation of fluid metabolic blobs (Metaballs). 30 iridescent fluid droplets merge and split dynamically, resembling a futuristic digital lava lamp. The scalar field is evaluated across the entire canvas, creating perfectly smooth, organic, cellular membranes that snap together when close.
- **Technique**: High-performance scalar field evaluation (Metaballs) using NumPy. For each pixel, the inverse-square distance to 30 kinetic points is accumulated. The resulting scalar energy field is mapped through a strict threshold and a vibrant color gradient, generating continuous, organic isosurfaces that merge and split. The rendering is done at 1080p internally and upscaled to 4K.
- **Format**: Animation (15s @ 60fps)

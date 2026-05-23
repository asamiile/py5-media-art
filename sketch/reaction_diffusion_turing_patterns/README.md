# reaction_diffusion_turing_patterns

The biological emergence of spots, stripes, and labyrinths through a simple Reaction-Diffusion system (Gray-Scott model) simulating Turing patterns.

- **Date**: 2026-05-23
- **Theme**: Turing patterns, reaction-diffusion, biological self-organization, Gray-Scott model.
- **Technique**: 2D Reaction-Diffusion PDE solved via finite difference method on a downscaled grid using `scipy.ndimage.convolve` for vectorized Laplacian operations. Chemical concentrations are iteratively updated across 8 sub-steps per frame. Feed and kill rates dynamically shift over time to transition the system from isolated spots to dense labyrinths and chaotic stripes. The resulting chemical field is upscaled and rendered directly to `py5.np_pixels` using a Deep Purple, Cyan, and Neon Orange color map. 15s 60fps MP4.
- **Description**: A mesmerizing, organic progression of life-like patterns. Starting from a dark purple void, vibrant cyan and neon orange chemical reactions spontaneously emerge, slowly growing into isolated cellular spots that gradually fuse, morph, and stretch into complex, shifting labyrinths resembling coral or animal skin.

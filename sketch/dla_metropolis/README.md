# Creative Brief: dla_metropolis

## 1. Concept Design
- **Theme**: Digital mineralization, organic urbanism, recursive growth, beautiful night sky.
- **Visual Impression**: A massive, fractal-like city growing in the void. It looks like a cross between a bismuth crystal and a futuristic megacity. Dark, jagged obsidian slabs are outlined in sharp neon light, floating in a dense, multi-magnitude starfield.
- **Aesthetic**: "Beautiful Night Sky" meets "Modern Brutalism". High contrast, deep blacks, vibrant cyan and amber accents.

## 2. Technical Implementation
- **Algorithm**: **3D Diffusion-Limited Aggregation (DLA)**. 
    - A "seed" starts at the center. 
    - Thousands of "wanderer" particles move via 3D Brownian motion.
    - When a wanderer touches the aggregated cluster, it "sticks" and becomes part of the city.
    - To speed up the simulation for a 10s animation, I will pre-calculate the growth or use a high-performance spatial hashing approach.
- **Rendering**:
    - **P3D** renderer.
    - **Architecture**: Each aggregated node is a `box()` primitive with dimensions based on its aggregation order (older = larger/taller).
    - **Highlights**: Use `py5.stroke()` with HSB mapping for neon edges.
    - **Starfield**: A high-density (5,000+ stars) background with subtle alpha-twinkling.
    - **Animation**: The city grows over time while the camera slowly orbits and zooms in, revealing the recursive complexity.
- **Optimization**: Use vectorized NumPy for the DLA logic and spatial checks.

## 3. Format: Animation (10s @ 60fps)
- **Resolution**: 1920x1080 (handled by `get_sizes()`).
- **Output**: `output.mp4`.
- **Preview**: `preview_p1.png` at frame 300.

# generative_synthwave_wireframe_landscape_3d

## Concept
A retro-futuristic 80s synthwave wireframe mountain landscape that infinitely scrolls towards the camera beneath a glowing digital sun.

## Technique
To ensure perfect rendering performance in a headless 4K environment without OpenGL context crashes, a custom math-driven 3D projection engine was built in NumPy. It generates a 120x120 NumPy heightmap grid infused with scrolling Perlin-like noise and manually projects the `(X, Y, Z)` coordinates into 2D perspective. The points are drawn as a sweeping neon wireframe that fades into the distance using `py5.vertices()`. A massive additive-blended sun with retro scanlines completes the background.

## Palette
- **Background**: Deep purple night sky
- **Primary**: Glowing neon purple/pink grid
- **Accent**: Blazing yellow/orange digital sun
- **Mood**: Nostalgic, retro-futuristic, 80s

## Format
Animation (450 frames @ 30fps)

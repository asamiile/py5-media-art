# Kinetic Orbital Spirograph Mandala 2D

## Description

A generative art piece created using `py5`. This sketch renders a highly complex, intricate spirograph mandala built from hundreds of interlocking orbital mechanics, tracing glowing geometric patterns in the void. It uses pure Python sine and cosine calculations to modulate the radius and angles of 200 translucent sweeping bezier curves that revolve and breathe over time.

## Technical Details

- **Renderer**: Default `py5` 2D renderer.
- **Motion**: Sine/cosine waves modulate radius and bezier control points to create complex orbital motion.
- **Visuals**: `py5.ADD` additive blending is used with a light trailing motion blur fade in `py5.BLEND` mode, causing the spirograph curves to glow brightly where they intersect.
- **Compilation**: 900 individual PNG frames are processed directly via `ffmpeg` into a 15-second continuous MP4.

## Output

- **Resolution**: 1920x1080
- **Framerate**: 60 FPS
- **Format**: MP4 (H.264, yuv420p)
- **Duration**: 15 seconds

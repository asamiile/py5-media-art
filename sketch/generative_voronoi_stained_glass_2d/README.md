# generative_voronoi_stained_glass_2d

## Concept
A stained glass window made of flowing, morphing mathematical cells. The cells pulse and shift continuously with deep, vibrant cathedral colors.

## Technique
Using `scipy.spatial.Voronoi` to dynamically re-calculate polygon tessellations around 300 floating centroid points at 30fps. The polygon vertices are fed into py5 to draw thick, dark "lead" outlines, while the fills are shaded dynamically based on a spatial sine-wave color function.

## Palette
- **Background**: Deep black (stained glass "lead")
- **Primary**: Deep ruby, sapphire, amethyst, and gold
- **Mood**: Ethereal, sacred, geometric

## Format
Animation (450 frames @ 30fps)

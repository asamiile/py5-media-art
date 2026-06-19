# generative_voronoi_stained_glass_fracture_2d

A 2D animation of a stained glass window that continuously fractures and morphs into new Voronoi cell shapes, illuminated by slowly shifting light colors.

## Theme
A slow-moving generative stained glass window fracturing and rebuilding itself.

## Technique
Used `scipy.spatial.Voronoi` to calculate cellular regions for seeds that drift using 2D Perlin noise. Cells are rendered with thick black borders, mimicking stained glass lead, and the inner hues shift over time with a dark vignette applied towards the edges.

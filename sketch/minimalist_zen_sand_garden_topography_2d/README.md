# minimalist_zen_sand_garden_topography_2d

An animated 15s sequence of minimalist generative topography lines slowly shifting, reminiscent of a zen sand garden or map contour lines.

## Theme
A 2D animation of minimalist generative topography lines slowly shifting, reminiscent of a zen sand garden or map contour lines.

## Technique
150 horizontal lines are drawn, consisting of 300 points each. The y-coordinate of each point is offset using `py5.os_noise`, creating a topographic map effect similar to Joy Division's Unknown Pleasures. The noise shifts over time, animating the peaks and valleys. The edges are smoothly tapered, and lines are filled below to occlude the lines drawn underneath.

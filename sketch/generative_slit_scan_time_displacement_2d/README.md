# generative_slit_scan_time_displacement_2d

**Date**: 2026-07-07
**Type**: Animation (10-30s @ 60fps)

## Concept
A digital slit-scan effect. A background scene consisting of moving abstract geometric shapes is drawn on a dense grid. However, the final output is composed such that each vertical strip (or grid cell) is sampled at a different point in time. This creates a bizarre time-displacement distortion where the left side of the screen shows the past and the right side shows the future.

## Techniques
A grid of 80x45 cells evaluates time as a function of the cell's X coordinate: `t_local = t_global - (x_index / cols) * max_delay`. Each cell draws nested shapes whose rotation, size, and hue depend on `t_local` and the Y coordinate. This pure mathematical approach creates the slit-scan visual perfectly in real-time without needing a massive pixel history buffer.

## Palette
High contrast chromatic aberration. The elements cycle continuously through the HSB color wheel, creating complex rainbow patterns that smear along the time-displaced X-axis.

# spider_web

**Theme**: nature, geometry, morning dew, organic structure, precision  
**Date**: 2026-04-26

## Description

An orb spider's web at dawn, beaded with dew drops. The web is constructed geometrically as real orb-weavers build it:

1. **Hub** — a small silk disc at the centre where all radial threads converge
2. **Radial threads** — 30–40 threads fanning outward to a frame polygon, with slight per-thread angle jitter and variable length for natural asymmetry
3. **Spiral rows** — 22–30 capture-silk rows spaced logarithmically from the hub to the frame; each row-segment is a quadratic Bézier that sags gently toward the centre under gravity
4. **Dew drops** — at ~80 % of spiral–radial intersections, a four-layer composited circle simulates a water droplet: outer glow → translucent body → bright core → white specular highlight offset for a convex-lens look

The entire web is randomised each run (n-radii, n-rows, centre position, individual thread lengths and angles) so every output is a unique web.

## Technique

- **Geometry**: logarithmic spiral row spacing `r_j = r₀ · (r_max/r₀)^(j/(N−1))`
- **Spiral sag**: quadratic bezier with control point displaced toward centre by factor `0.962 + 0.025·frac`
- **Dew drop**: four concentric circles with decreasing radius and increasing opacity; 210-alpha specular highlight
- **py5 drawing**: `begin_shape / quadratic_vertex / end_shape` for bezier spiral segments

## Parameters

| Constant | Range |
|---|---|
| Radial threads | 30–40 |
| Spiral rows | 22–30 |
| Web radius | 44–46% of min(W, H) |
| Hub radius | 7–11% of web radius |
| Dew coverage | ~80% of intersections |
| Preview size | 1920 × 1080 |
| Output size | 3840 × 2160 |

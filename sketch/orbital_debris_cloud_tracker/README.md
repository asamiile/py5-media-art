# orbital_debris_cloud_tracker

**Date**: 2026-05-26
**Format**: Animation (15s @ 60fps)

## Concept
A procedural radar scope tracking tens of thousands of space debris fragments orbiting in a massive 3D cloud.

## Technique
Uses `py5.points()` with numpy vectorization to handle 45,000 points in real-time, grouped into orbital shells based on Keplerian distribution. Points are colored based on proximity and velocity to simulate critical alerts.

## Notes
- Smooth rendering at 60fps thanks to numpy optimization.
- HUD elements track total object count and sweep angle.

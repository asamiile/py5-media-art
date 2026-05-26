# water_treatment_clarifier

- **Date**: 2026-05-26
- **Type**: 10s animation, 4K/60fps MP4
- **Preview**: `water_treatment_clarifier_p1.png`
- **Video**: `water_treatment_clarifier.mp4`

## Concept

A circular wastewater clarifier becomes a kinetic instrument: rake arms sweep through blue-green water, suspended floc settles toward a sludge floor, and a turbidity panel tracks inlet, rake, and effluent signals.

## Technique

The animation is rendered headlessly with Pillow geometry. It layers elliptical tank bands, rotating bridge arms, hundreds of drifting floc particles, and oscilloscope-style process traces before encoding a 10-second 4K H.264 loop with ffmpeg.

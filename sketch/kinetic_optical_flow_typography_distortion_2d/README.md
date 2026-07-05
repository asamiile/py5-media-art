# kinetic_optical_flow_typography_distortion_2d

**Date**: 2026-07-05
**Type**: Animation (10-30s @ 60fps)

## Concept
Large, bold typography slowly scrolling or flashing on screen, while being dynamically distorted by an invisible optical flow field. It creates the illusion of text melting, smearing, and being pulled through a viscous fluid.

## Techniques
Uses a hidden buffer where text is rendered cleanly. A 2D noise field (Perlin) creates flow vectors. The main sketch samples the hidden buffer, offset by the flow vectors, and redraws it with slight alpha fading, leading to a feedback loop of text melting across the screen.

## Palette
Cyberpunk data corruption. Bright yellow and cyan text over a deep CRT-glitched scanline background.

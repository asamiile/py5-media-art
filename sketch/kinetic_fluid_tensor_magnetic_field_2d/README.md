# kinetic_fluid_tensor_magnetic_field_2d

**Date**: 2026-07-05
**Type**: Animation (10-30s @ 60fps)

## Concept
A generative simulation of iron filings being pushed around by a massive set of shifting magnetic dipoles, but rendered with smooth, flowing tensors rather than discrete lines. It produces an intricate, silky, high-contrast magnetic interference pattern.

## Techniques
Calculates the magnetic vector field from 20 moving dipoles. Instead of discrete particles, it evaluates a high-resolution 2D grid of field lines using a localized Line Integral Convolution (LIC) technique or a smooth vector field tracer that draws overlapping translucent curves. The curves twist and align to the magnetic field.

## Palette
Deep obsidian black background. The field lines are glowing copper, gold, and deep bronze, mapping to the field intensity.

# chromatic_drift

A generative visualization of the ethereal separation of light and memory as it drifts through a prismatic medium.

![preview](preview.png)

## Concept

This artwork explores the idea of "chromatic memory"—the notion that light, as it passes through time and space, doesn't just travel but also fractures and leaves behind a spectral trace. It uses a multi-channel particle system where the Red, Green, and Blue components of light are treated as independent agents, each with its own slightly offset physics, leading to a slow, graceful separation of pure color.

## Technique

- **Multi-Channel Agents**: 15,000 independent agents (5k per R, G, B channel) navigate a large-scale noise flow field.
- **Prismatic Separation**: Each color channel is driven by a slightly offset noise phase and has different speed/drag parameters, causing the "prismatic" pulling apart of light streaks.
- **Cumulative Light**: Uses a very slow background fade and SCREEN blending to accumulate light over time, creating a hazy, long-exposure "fog" of color.
- **Refractive Flashes**: Occasional large-scale additive pulses simulate the light hitting a refractive boundary, adding depth to the atmospheric void.
- **Stochastic Flares**: Individual particles have a small chance to "flare up" (increased alpha), creating momentary focal points.

## Data

- **Date**: 2026-05-02
- **Theme**: Synesthesia, Optics, Memory, Pure Abstraction
- **Technique**: Multi-channel particle system, Noise flow field, SCREEN blending, Long exposure
- **Format**: 6s Animation @ 60fps (MP4)

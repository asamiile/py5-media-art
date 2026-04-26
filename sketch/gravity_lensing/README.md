# gravity_lensing

**Theme**: space, physics, general relativity, optics, black hole  
**Date**: 2026-04-26

## Description

A black hole rendered through the mathematics of gravitational lensing. For each pixel on the canvas, the thin-lens deflection formula (α = r_E² / r) bends light rays back to their unlensed origin in a synthetic star field, recreating the visual signature of a massive compact object:

- **Einstein ring** — a golden circle of light where rays from directly behind the lens are bent into a complete arc
- **Event horizon** — a pitch-black disk where light cannot escape
- **Photon sphere** — a faint blue-white halo at 1.6× the horizon radius
- **Accretion disk** — an orange-white glowing band of infalling matter, with Doppler brightening on the approaching (left) side

The starfield is built from 8000 stars scattered with exponential brightness distribution, color-temperature variation (warm orange to blue-white), gaussian point-spread glow, and cross-shaped diffraction spikes on the brightest sources — evoking the look of deep space imagery through a telescope.

## Technique

- **Thin-lens deflection**: α = r_E² / r² · (dx, dy); bilinear interpolation via `scipy.ndimage.map_coordinates`
- **Amplification ring**: intensity boost ∝ exp(−(|r − r_E| / σ)²) around Einstein radius
- **Accretion disk**: radial Gaussian band with vertical falloff and Doppler asymmetry
- **Tone mapping**: 99.5th-percentile normalization + γ = 0.80 power curve + mild vignette

## Parameters

| Constant | Value |
|---|---|
| Einstein radius | 21% of canvas height |
| Event horizon | 4.4% of canvas height |
| Stars | 8000, exponential brightness |
| Preview size | 1920 × 1080 |
| Output size | 3840 × 2160 |

# water_caustics

**Theme**: water, light, optics, physics, swimming pool, refraction  
**Date**: 2026-04-26

## Description

The shimmering golden web of light seen on the floor of a sunlit swimming pool — simulated from first principles. Sunlight is modelled as a uniform vertical ray for every pixel of the water surface. Each ray is refracted using the full vector form of Snell's law (n_air/n_water = 1/1.333), then projected onto a virtual pool floor. Where many refracted rays converge, the floor glows bright (a **caustic**); where rays diverge, it dims.

The water surface is a superposition of 8 random sinusoidal waves with wavelengths 90–260 px and amplitudes 3.5–9 px. Surface normals are computed analytically (no finite-difference noise). The resulting photon density histogram is tone-mapped in three zones:

- **Dark floor** — near-black navy where few rays arrive
- **Caustic glow** — warm gold where rays converge moderately
- **Hot flare** — near-white bloom at the brightest caustic nodes

A subtle square tile grid is composited underneath, giving the floor a ceramic texture.

## Technique

- **Wave surface**: analytic sum of 8 sinusoids; gradients computed symbolically (∂h/∂x, ∂h/∂y)
- **Snell's law (vector form)**: T = n_rel·I + (n_rel·cos_θᵢ − cos_θₜ)·N̂
- **Density accumulation**: `np.bincount` on integer floor coordinates (no loops)
- **Tone mapping**: two-layer piecewise — glow `density/4.5` + flare `(density−4.5)/25`
- **Smoothing**: `gaussian_filter(σ=1.2)` to remove aliasing without blurring caustic lines

## Parameters

| Constant | Value |
|---|---|
| Wave count | 8 |
| Wavelength range | 90–260 px |
| Amplitude range | 3.5–9 px |
| Pool depth | 55% of canvas height |
| Refractive index | 1.333 (water) |
| Preview size | 1920 × 1080 |
| Output size | 3840 × 2160 |

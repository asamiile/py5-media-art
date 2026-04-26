# soap_film

**Theme**: optics, thin-film interference, iridescence, light, physics  
**Date**: 2026-04-26

## Description

The iridescent colour field seen on a soap bubble or oil slick — simulated from the physics of thin-film optics. A soap film of thickness *t* at refractive index *n* = 1.34 reflects two partial waves: one from the air→soap interface (with a π phase shift) and one from the soap→air interface (no phase shift). Their interference produces wavelength-selective reflection:

    I(λ) = ½ · (1 − cos(4π·n·t / λ))

The film thickness *t* is drawn from a 6-octave fractional Brownian motion field biased with a top-to-bottom gravity drain. At each pixel, this formula is evaluated for 21 wavelengths across the visible spectrum (380–780 nm), weighted by approximate CIE sensitivity curves, and summed into RGB. A saturation boost separates the chromatic deviation from the achromatic mean; a power-law tone map compresses mid-tones; and an oval vignette frames the result.

The resulting swirling colour pattern follows the classic Newton's interference colour sequence — black film → grey → first-order violet/blue → green → yellow/orange/red → second-order violet → … — distributed across the organic fBm contours. Every run produces a unique configuration.

## Technique

- **Surface**: 6-octave fBm (3 random sinusoids per octave), range 0–680 nm
- **Physics**: thin-film reflectance I(λ) = ½·(1−cos(4πnt/λ)) with correct π reflection phase
- **Spectral integration**: 21 wavelengths × CIE Gaussian sensitivity curves → RGB
- **Colour treatment**: `rgb + 2·(rgb−mean)` saturation boost · power-law γ = 1.35
- **Framing**: oval vignette to evoke the curvature of a soap bubble

## Parameters

| Constant | Value |
|---|---|
| Refractive index | 1.34 (soap-water solution) |
| Thickness range | 0–680 nm (≈2.5 interference orders) |
| Wavelength samples | 21 (380–780 nm, step 20 nm) |
| fBm octaves | 6 |
| Preview size | 1920 × 1080 |
| Output size | 3840 × 2160 |

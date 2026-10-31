# kinetic_rutt_etra_scan_processor_synthesis_2d

Autonomous generative media art animation simulating the 1973 Rutt-Etra Video Synthesizer and early video scan processing art in 4K UHD 60fps (12.0s seamless loop).

## Concept

Pioneered in 1973 by Louise and Bill Etra with Steve Rutt, and famously utilized in the electronic video art of Steina and Woody Vasulka (*The Matter*, *Time/Energy Objects*), the Rutt-Etra Video Synthesizer used analog operational amplifiers to vertically deflect the electron beam raster scanlines of a CRT cathode-ray tube based on luminance voltage.

This artwork translates the analog circuitry of scan processing into modern computational geometry:
1. **Voltage-Controlled 3D Raster Topography**:
   150 horizontal scanlines with 360 sub-carrier samples are projected into oblique 3D space. Tri-harmonic video voltage oscillators (radial Bessel ripples, chiral spiral waves, and orthogonal standing wave carriers) deflect the scanlines into undulating, folding topographic video mountains.
2. **Tri-Channel RGB Chromatic Aberration & Time Delay**:
   Simulating analog video colorizers (such as the Sandin Image Processor), the luminance signal is split into three RGB channels with temporal phase lead/lag offsets ($\pm 12\text{ ms}$), creating vibrant chromatic fringing along high-gradient deflection slopes.
3. **P22 Phosphor Persistence & Blooming**:
   Dual-pass raster stroke rendering combines a wide translucent phosphor halo glow with an ultra-bright, laser-crisp electron beam core.
4. **Horizontal Sync Glitch Slices**:
   Periodic tracking jitter slices simulate analog phase-locked loop (PLL) tracking flutter and horizontal sync instability.
5. **Auxiliary Waveform Instrumentation**:
   - **Top-Left**: NTSC Vectorscope monitoring subcarrier constellation phase vectors.
   - **Top-Right**: XY Oscilloscope tracing a 3:2 Lissajous harmonic audio knot.
   - **Bottom**: A-Scan Waveform Monitor measuring peak-to-peak video voltage (IRE 100).
   - **Frame**: Curved CRT tube chassis bezel, aperture grille horizontal shadow lines, and calibration crosshairs.

## Technical Specifications

- **Resolution**: 3840 × 2160 (4K UHD)
- **Framerate**: 60 fps
- **Duration**: 720 frames (12.0s seamless loop)
- **Loop Mathematics**: All oscillator frequencies $\omega_i = k_i \cdot \frac{2\pi}{T}$ with integer multipliers $k_i \in \{9, 3, 6, 2, 4, 5\}$, guaranteeing that frame 0 and frame 720 are mathematically identical.
- **Color Palette**:
  - CRT Chassis Deep Phosphor Black (`#040609`)
  - P22 Phosphor Emerald Green (`#22c55e` / `#4ade80`)
  - Chromatic Aberration Red/Magenta (`#f43f5e`)
  - Chromatic Lag Royal Blue (`#2563eb`)
  - Vector Oscilloscope Cyan (`#06b6d4`)
  - Waveform IRE Amber (`#f59e0b`)
- **Strict Anonymity**: 100% autonomous algorithmic generative art without human authorship marks, artist signatures, monograms, initials, or personal seals.

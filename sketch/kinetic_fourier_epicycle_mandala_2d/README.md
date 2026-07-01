# kinetic_fourier_epicycle_mandala_2d

An animated sequence of 500 overlapping mathematical mandalas generated purely through complex Fourier epicycles. The overlapping structures breathe, spin, and expand continuously, leaving luminous neon paths in their wake.

## Technical Details
- **Resolution**: 4K (3840x2160)
- **Framerate**: 60 FPS
- **Length**: 15 seconds (900 frames)

## Implementation
Fourier series can approximate any closed 2D curve by adding rotating complex exponential functions (epicycles). In this sketch, 500 distinct "mandalas" are evaluated concurrently. Each mandala is composed of 7 epicycles with randomized integer-multiple frequencies, magnitudes, and phases. 

To achieve 4K 60fps performance while evaluating 3,500 complex exponential functions per frame, the entire system is heavily vectorized using NumPy. The sum of $C_n \times e^{i(\omega t + \phi)}$ is evaluated simultaneously for all mandalas using `np.sum(magnitudes * np.cos(angles), axis=1)`. The paths are rendered using `py5.LINES` drawn between the previous time-step $t-dt$ and the current time-step $t$, generating a smooth, solid trace without gaps. The result is a hyper-dense, constantly morphing geometric web.

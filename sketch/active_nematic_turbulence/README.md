# active_nematic_turbulence

An autonomous, physics-driven generative media art piece visualizing the chaotic, self-sustained dynamics of active nematic liquid crystals.

![active_nematic_turbulence_p1](active_nematic_turbulence_p1.png)

## Creative Brief

- **Theme**: The restless, self-sustained dance of active living matter, where microscopic energy sources continuously drive chaotic flows, tearing order apart into wandering topological defects that seek each other in the dark.
- **Visual Impression**: A dark Prussian blue liquid chamber filled with a highly structured, fibrous mesh of glowing teal filaments. Active forces buckle the filaments into beautiful, swirling vortex streams, spawning blinding golden comets (+1/2 defects) and electric pink stars (-1/2 defects) that sail and slide through the fluid, leaving glowing trails of amethyst light.
- **Color Palette**:
  - Background: Deep Midnight Prussian Blue (`#050813`)
  - Dominant (60%): Luminous teal and electric ocean-blue filaments (`#1ed5d9`, `#0b8da8`) representing the nematic director flow.
  - Secondary (30%): Deep amethyst and royal violet trails (`#781eb8`, `#410d6b`) visualizing local fluid shear and vorticity.
  - Accent (10%): Blinding sun-gold (`#ffd700`) for the +1/2 cometary defects and electric hot pink (`#ff1493`) for the -1/2 star defects.

## Technical Details

This artwork implements a fully coupled 2D active nematodynamics simulation:

1. **Q-tensor Representation**:
   To avoid singular derivatives and phase wrapping artifacts during advection and diffusion, the nematic director field $\theta(x, y)$ is evolved via the symmetric traceless Q-tensor components:
   $$Q_1 = Q_{xx} = \cos(2\theta), \quad Q_2 = Q_{xy} = \sin(2\theta)$$

2. **Active Force Density**:
   Microscopic energy injection generates active stress proportional to the divergence of the Q-tensor. For extensile active stress ($\alpha < 0$), this drives localized forces:
   $$f_x = \alpha (\partial_x Q_1 + \partial_y Q_2), \quad f_y = \alpha (\partial_x Q_2 - \partial_y Q_1)$$

3. **Incompressible Screened Stokes Flow**:
   The fluid velocity field $\mathbf{u} = (u_x, u_y)$ satisfies low-Reynolds screened Stokes dynamics under substrate friction:
   $$\mathbf{u} - \lambda^2 \nabla^2 \mathbf{u} + \nabla p = \mathbf{f}_a, \quad \nabla \cdot \mathbf{u} = 0$$
   This is solved exactly and periodically in Fourier space using 2D Fast Fourier Transforms (FFT):
   $$\hat{\mathbf{u}}(\mathbf{k}) = \frac{1}{1 + \lambda^2 k^2} \left( \hat{\mathbf{f}}_a - \frac{\mathbf{k} \cdot \hat{\mathbf{f}}_a}{k^2} \mathbf{k} \right)$$

4. **Director Advection & Flow Coupling**:
   The Q-tensor is advected by the velocity field and rotated by the local fluid vorticity $\omega = \partial_x u_y - \partial_y u_x$ and shear strain rate tensor $\mathbf{D}$:
   $$\partial_t \mathbf{Q} + (\mathbf{u} \cdot \nabla) \mathbf{Q} = \Gamma \nabla^2 \mathbf{Q} + \mathbf{S}_{rot}(\mathbf{Q}, \omega, \mathbf{D})$$

5. **Topological Defect Tracking**:
   Topological defects are identified by computing the winding number (topological charge) $q$ around each $2\times2$ grid cell:
   $$q = \frac{1}{2\pi} \oint \nabla \theta \cdot d\mathbf{r}$$
   - **$+1/2$ Defects** (winding $q \approx +1/2$) are cometary-shaped and swim actively along their symmetry axis, highlighted as glowing sun-gold comets.
   - **$-1/2$ Defects** (winding $q \approx -1/2$) possess three-fold rotational symmetry and drift passively, drawn as electric hot pink three-spoked stars.

6. **Tracer Particles**:
   120,000 passive tracers are advected by the velocity field via bilinear interpolation. They are drawn as short, aligned fiber segments in three distinct HSB-tailored color bins under additive blending, leaving gorgeous glowing ribbons in the deep water.

## Execution

The script renders a 15-second, 4K/60fps MP4 animation:
```bash
uv run python main.py
```
This automatically compiles the individual frames into `active_nematic_turbulence.mp4` via FFmpeg and copies the mid-frame to `active_nematic_turbulence_p1.png` as the portfolio preview.

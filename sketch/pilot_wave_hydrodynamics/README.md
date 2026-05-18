# pilot_wave_hydrodynamics

An autonomous, physics-driven generative media art piece visualizing the chaotic, self-guided dynamics of Faraday wave walking droplets (hydrodynamic pilot-wave memory).

![pilot_wave_hydrodynamics_p1](pilot_wave_hydrodynamics_p1.png)

## Creative Brief

- **Theme**: Path memory and wave-particle duality in classical physics. A microscopic droplet bouncing on a vertically vibrating fluid bath generates local standing Faraday wave ripples that serve as its own guiding field. The droplet is deflected by the gradients of its own past waves, creating a self-guided chaotic walk fueled by wave memory.
- **Visual Impression**: A dark, metallic pool. 8 brilliant white-pearl droplets bounce periodically, spawning concentric neon turquoise ripples that propagate and interfere. The droplets cruise across the pool, steered by the invisible slopes of the wave field, tracing golden dashed trajectories that reveal the quantum-like path memory of their motion.
- **Color Palette**:
  - Background: Metallic obsidian and dark graphite (`#0b0c10`)
  - Waves (Fresh): Glowing neon turquoise (`#00ffcc`) and electric cyan (`#00f5ff`)
  - Waves (Decaying): Deep royal indigo and violet (`#6600ff`, `#2a0066`)
  - Droplets: Brilliant white-pearl cores with a golden halo (`#ffffff`, `#ffd700`)
  - Trails: Faint, shimmering amber-gold path lines (`#cca300`)

## Technical Details

This artwork implements a fully coupled pilot-wave / walking droplet simulation:

1. **Faraday Standing Wave Superposition**:
   Instead of solving a heavy 2D wave equation PDE (which doesn't preserve infinite-depth standing wave-memory cleanly), the surface wave field $H(x, y, t)$ is modeled as a superposition of decaying circular Faraday wave ripple profiles deposited at each droplet impact:
   $$h_i(r, t - t_i) = A_0 e^{-\beta_{decay} (t - t_i)} \cos(\omega_F (t - t_i)) \cos(k_F r) e^{-r^2 / 2\sigma^2}$$
   where $r$ is the distance to the bounce position $\mathbf{x}_i$, and $t_i$ is the bounce timestamp.

2. **Slope-Coupled Dynamics**:
   The droplet agents bounce periodically, with their height above the fluid modeled as:
   $$z(t) = |\sin(\omega_B t + \phi_0)|$$
   Upon impact ($z(t) \approx 0$), they read the local gradients of the wave field and receive a lateral deflection kick down the wave slope:
   $$v_x \leftarrow v_x - \gamma_k \partial_x H(\mathbf{x}_p), \quad v_y \leftarrow v_y - \gamma_k \partial_y H(\mathbf{x}_p)$$
   A drag force acts to limit the kinetic energy, and thermal fluctuations drive chaotic trajectories.

3. **High-Performance Hybrid Rendering**:
   - **Low-resolution Fluid Surface**: The wave height $H(x, y)$ is evaluated on a $256 \times 256$ grid. Shading calculations (gradients, specular lighting, and color mapping) are fully vectorized in NumPy (running in $<2$ms).
   - **Bilinear Upscaling**: The shaded 256x256 image is drawn stretched to the full canvas resolution (`1920x1080`) using hardware-accelerated bilinear scaling (`py5.image`), making the fluid waves look smooth, organic, and perfectly liquid.
   - **High-resolution Vector Overlays**: The bouncing pearl droplets (with size modulated by altitude $z$) and their glowing amber path-memory dashed trails are rendered at native 1080p, guaranteeing razor-sharp details.

4. **ARGB Packed Color Mapping**:
   To prevent signed 32-bit integer overflow issues in macOS, colors are packed into ARGB format using `np.uint32` and then cast back to `np.int32` before writing to `py5_img.pixels`:
   $$\text{Packed} = \text{int32}(0\text{xff000000} \mid (R_{\text{uint32}} \ll 16) \mid (G_{\text{uint32}} \ll 8) \mid B_{\text{uint32}})$$

## Execution

The script renders a 15-second, 4K/60fps MP4 animation:
```bash
uv run python main.py
```
This automatically compiles the individual frames into `pilot_wave_hydrodynamics.mp4` via FFmpeg and copies the mid-frame to `pilot_wave_hydrodynamics_p1.png` as the portfolio preview.

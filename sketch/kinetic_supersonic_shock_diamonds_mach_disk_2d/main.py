from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 18
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Spatial Simulation Grid (16:9 aspect ratio)
# Using 640x360 grid for vectorized field calculations, upscaled smoothly to 4K
Nx, Ny = 640, 360
x_coords = np.linspace(-4.4, 4.4, Nx, dtype=np.float32)
y_coords = np.linspace(-4.4 * (Ny / Nx), 4.4 * (Ny / Nx), Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Lagrangian Supersonic Plasma Tracer Particles
MAX_PARTICLES = 1200
particles = []


class PlasmaParticle:
    def __init__(self, px, py, is_core=True):
        self.px = px
        self.py = py
        self.prev_x = px
        self.prev_y = py
        self.vx = 0.0
        self.vy = 0.0
        self.is_core = is_core
        self.life = random.uniform(80.0, 240.0) if is_core else random.uniform(90.0, 280.0)
        self.max_life = self.life
        self.radius = random.uniform(1.4, 3.2) if is_core else random.uniform(1.0, 2.2)
        self.temp = 1.0 if is_core else random.uniform(0.3, 0.7)

    def update(self, flow_vx, flow_vy, shock_boost, dt=1.0):
        self.prev_x = self.px
        self.prev_y = self.py

        if self.is_core:
            # Core particles accelerate downstream through shock cells
            target_vx = flow_vx * (1.8 + shock_boost * 1.5)
            target_vy = flow_vy * 1.2
            self.vx = self.vx * 0.88 + target_vx * 0.12
            self.vy = self.vy * 0.88 + target_vy * 0.12
            self.temp = min(1.0, self.temp * 0.985 + shock_boost * 0.4)
        else:
            # Shear layer particles entrained in turbulent vortices
            target_vx = flow_vx * 0.9
            target_vy = flow_vy * 1.4
            self.vx = self.vx * 0.91 + target_vx * 0.09
            self.vy = self.vy * 0.91 + target_vy * 0.09
            self.temp = max(0.1, self.temp * 0.99)

        self.px += self.vx * dt
        self.py += self.vy * dt
        self.life -= 1.0

    @property
    def is_dead(self):
        return (
            self.life <= 0
            or self.px > py5.width + 120
            or self.px < -80
            or self.py > py5.height + 80
            or self.py < -80
        )


def compute_supersonic_flow_fields(frame):
    """
    Computes compressible aerodynamics of an underexpanded supersonic jet:
    - Multi-cell diamond shock structure
    - Normal Mach disk stems and triple points
    - Reflected oblique shocks and expansion fans
    - Acoustic screech oscillation & shear layer Kelvin-Helmholtz roll-up
    - Schlieren density gradient optics
    """
    t = frame / 60.0  # seconds

    # Screech feedback mode: acoustic resonance breathing
    screech_freq = 0.85  # Hz
    screech_phase = 2.0 * np.pi * screech_freq * t
    screech_amp = 0.045 * np.sin(screech_phase)

    # Jet geometry parameters
    nozzle_exit_x = -2.85
    nozzle_exit_r0 = 0.42

    # Jet boundary envelope: initial Prandtl-Meyer expansion, cell bulging, turbulent spreading
    X_rel = X_grid - nozzle_exit_x
    jet_active_mask = X_rel >= -0.05

    # Core shock cell wavelength
    L_cell = 1.12 + screech_amp * 0.8

    # Spreading rate of the shear layer: linear growth plus smooth transition
    plume_dist = np.maximum(0.0, X_rel)
    plume_fade = np.clip(1.0 - (plume_dist / 6.2)**2.2, 0.0, 1.0)
    shear_spread = 0.088 * plume_dist
    cell_modulation = 0.055 * np.sin(2.0 * np.pi * plume_dist / L_cell) * np.exp(-0.22 * plume_dist)
    R_jet = nozzle_exit_r0 + 0.14 * (1.0 - np.exp(-1.4 * plume_dist)) + cell_modulation + shear_spread

    # Normalized radial distance across jet
    Eta = np.abs(Y_grid) / (R_jet + 1e-4)

    # Core boundary factor (smooth hyperbolic tangent transition)
    core_mask = np.where(jet_active_mask, 0.5 * (1.0 - np.tanh((Eta - 1.0) * 2.8)) * plume_fade, 0.0)

    # 1. Oblique Shock Diamonds & Mach Disks Synthesis
    # A chain of 5 diamond cells with continuous decay and blending
    diamond_shocks = np.zeros_like(X_grid)
    mach_disks = np.zeros_like(X_grid)
    post_shock_heat = np.zeros_like(X_grid)
    slip_lines = np.zeros_like(X_grid)

    num_cells = 5
    for k in range(num_cells):
        decay = np.exp(-0.35 * k)
        cell_x0 = nozzle_exit_x + k * L_cell
        cell_xc = cell_x0 + 0.5 * L_cell
        cell_x1 = cell_x0 + L_cell

        # Incident oblique shock front
        x_incline = (X_grid - cell_x0) / (0.52 * L_cell)
        target_y_incident = nozzle_exit_r0 * (1.0 - np.clip(x_incline, 0.0, 1.0)) * (0.92 - 0.04 * k)
        dist_incident = np.abs(np.abs(Y_grid) - target_y_incident)
        shock_incident = np.exp(- (dist_incident**2) / 0.004) * np.logical_and(X_grid >= cell_x0, X_grid <= cell_xc + 0.1)

        # Reflected oblique shock front radiating outward from Mach stem
        x_reflected = (X_grid - cell_xc) / (0.52 * L_cell)
        target_y_reflected = nozzle_exit_r0 * np.clip(x_reflected, 0.0, 1.0) * (0.88 - 0.04 * k)
        dist_reflected = np.abs(np.abs(Y_grid) - target_y_reflected)
        shock_reflected = np.exp(- (dist_reflected**2) / 0.005) * np.logical_and(X_grid >= cell_xc - 0.05, X_grid <= cell_x1)

        # Smooth taper at cell boundaries to eliminate harsh square cuts
        window_in = np.clip((X_grid - cell_x0) / 0.12, 0.0, 1.0)
        window_out = np.clip((cell_x1 - X_grid) / 0.18, 0.0, 1.0)
        cell_window = window_in * window_out

        cell_diamond = (shock_incident * 1.15 + shock_reflected * 0.95) * cell_window * decay
        diamond_shocks += cell_diamond

        # Mach disk (normal shock stem) at the cell neck
        mach_stem_r = max(0.035, (0.15 - 0.024 * k) * decay)
        mach_disk_x = cell_xc + screech_amp * 0.25
        dx_mach = (X_grid - mach_disk_x) / 0.032
        dy_mach = np.abs(Y_grid) / mach_stem_r
        mach_stem = np.exp(-0.5 * (dx_mach**2)) * np.maximum(0.0, 1.0 - dy_mach**2) * decay
        mach_disks += mach_stem

        # Post-shock high-temperature subsonic recirculation core
        core_heat = np.exp(- ((X_grid - (cell_xc + 0.16))**2) / 0.055 - (Y_grid**2) / 0.035) * decay
        post_shock_heat += core_heat

        # Slip line contact discontinuities originating from the triple points
        slip_y = mach_stem_r * 0.95
        dist_slip = np.abs(np.abs(Y_grid) - slip_y)
        slip_taper = np.clip((cell_x1 + 0.35 - X_grid) / 0.25, 0.0, 1.0)
        slip = np.exp(- (dist_slip**2) / 0.003) * np.logical_and(X_grid >= cell_xc, X_grid <= cell_x1 + 0.35) * slip_taper * decay
        slip_lines += slip

    # 2. Prandtl-Meyer Expansion Fans & Continuous Core Plasma Stream
    # Periodic expansion waves and continuous supersonic core flow
    core_axial_stream = np.exp(- (Y_grid**2) / (0.18 * (R_jet**2) + 1e-4)) * core_mask
    expansion_wave = 0.5 * (1.0 + np.sin(2.0 * np.pi * (plume_dist - 0.22 * L_cell) / L_cell + screech_phase * 0.5))
    expansion_field = expansion_wave * core_mask * np.exp(-0.16 * plume_dist)

    # 3. Turbulent Shear Layer: Continuous Undulating Streamlines & Vortex Filaments
    # Smooth convective waves along upper and lower shear boundaries instead of isolated spots
    kh_freq = 2.4
    convective_phase = 2.0 * np.pi * (kh_freq * t - 0.9 * plume_dist)
    shear_gaussian = np.exp(- ((Eta - 1.0)**2) / 0.15) * np.exp(- ((Eta - 1.0)**4) / 0.2)
    # Continuous undulating streamline wave
    kh_streamlines = (
        0.55 * np.sin(convective_phase)
        + 0.30 * np.sin(2.0 * convective_phase + 0.7)
        + 0.15 * np.cos(0.5 * convective_phase)
    ) * shear_gaussian * np.clip(plume_dist / 0.6, 0.0, 1.0) * plume_fade * jet_active_mask

    # 4. Total Density Field & Directional Schlieren Optics
    rho_base = np.where(X_grid < nozzle_exit_x, 2.6, 0.35 + 0.65 * core_axial_stream)
    rho_total = (
        rho_base
        + 1.35 * diamond_shocks
        + 2.4 * mach_disks
        + 0.75 * slip_lines
        - 0.3 * expansion_field
        + 0.35 * kh_streamlines
    )

    # Schlieren knife-edge gradient magnitude: ||grad(rho)||
    grad_y, grad_x = np.gradient(rho_total, y_coords[1] - y_coords[0], x_coords[1] - x_coords[0])
    schlieren_mag = np.sqrt(grad_x**2 + grad_y**2)
    schlieren_norm = np.clip(schlieren_mag / 7.8, 0.0, 1.0)

    # 5. Flow Velocity Vector Field for Particle Advection
    u_axial = np.where(
        jet_active_mask,
        core_mask * (4.2 - 1.4 * mach_disks - 0.7 * diamond_shocks) + (1.0 - core_mask) * 0.45,
        0.05
    )
    v_radial = np.where(
        jet_active_mask,
        -np.sign(Y_grid) * core_mask * 0.45 * np.sin(2.0 * np.pi * plume_dist / L_cell) + 0.25 * kh_streamlines,
        0.0
    )

    return (
        core_mask,
        core_axial_stream,
        diamond_shocks,
        mach_disks,
        post_shock_heat,
        slip_lines,
        expansion_field,
        kh_streamlines,
        schlieren_norm,
        u_axial,
        v_radial,
        R_jet,
        nozzle_exit_x,
    )


def render_supersonic_canvas(
    core_mask,
    core_axial_stream,
    diamond_shocks,
    mach_disks,
    post_shock_heat,
    slip_lines,
    expansion_field,
    kh_streamlines,
    schlieren_norm,
    nozzle_exit_x,
    frame,
):
    """
    Renders the composite 4-channel image into pixel_buffer using strict 60-30-10 palette rules:
    - 60% Abyssal Void & Supersonic Expansion Cobalt/Indigo (#030712, #0b192c, #152238)
    - 30% Ionized Shock Cyan & Electric Teal (#00f0ff, #38bdf8, #06b6d4)
    - 10% Incandescent Mach Disk White-Gold, Solar Amber, & Plasma Core Violet
    """
    # Base background: Deep cosmic vacuum exhaust void with subtle horizontal vignette
    bg_r = 3.0 + 2.0 * np.cos(X_grid * 0.3)
    bg_g = 7.0 + 4.0 * np.cos(X_grid * 0.25)
    bg_b = 18.0 + 8.0 * np.sin(X_grid * 0.2 + 0.5)

    # Dominant 60%: Supersonic expansion indigo / deep cobalt glow + continuous supersonic stream
    plume_base = core_mask * 0.75 + core_axial_stream * 0.45
    r_dom = bg_r + plume_base * 14.0 + expansion_field * 8.0
    g_dom = bg_g + plume_base * 32.0 + expansion_field * 24.0
    b_dom = bg_b + plume_base * 85.0 + expansion_field * 50.0

    # Secondary 30%: Ionized Shock Diamonds, Slip Lines, Schlieren, and Shear Streamlines
    # Electric Cyan (#00f0ff) & Bright Sky Blue (#38bdf8)
    cyan_intensity = (
        diamond_shocks * 1.35
        + slip_lines * 1.15
        + schlieren_norm * 0.95
        + np.maximum(0.0, kh_streamlines) * 0.9
        + np.maximum(0.0, -kh_streamlines) * 0.45
    )
    cyan_r = cyan_intensity * 10.0
    cyan_g = cyan_intensity * 215.0
    cyan_b = cyan_intensity * 255.0

    # Accent 10%: Incandescent Mach Disk Core White-Gold & Plasma Violet
    # Pure incandescent white center with amber halo and violet ionization edge
    mach_intensity = mach_disks * 1.65 + post_shock_heat * 1.1
    # White-Gold core (#ffffff, #fef08a, #f59e0b)
    accent_r = mach_intensity * 255.0 + post_shock_heat * 70.0
    accent_g = mach_intensity * 245.0 - post_shock_heat * 30.0
    accent_b = mach_intensity * 185.0 + post_shock_heat * 130.0

    # Composite layers
    R_total = np.clip(r_dom + cyan_r + accent_r, 0.0, 255.0)
    G_total = np.clip(g_dom + cyan_g + accent_g, 0.0, 255.0)
    B_total = np.clip(b_dom + cyan_b + accent_b, 0.0, 255.0)

    # Rocket Nozzle Bell Structure on the left (X < nozzle_exit_x)
    nozzle_lip_x = nozzle_exit_x
    dx_nozzle = X_grid - nozzle_lip_x
    in_nozzle_region = dx_nozzle <= 0.05
    y_bell = 0.42 + 0.38 * (dx_nozzle**2)
    nozzle_metal_wall = np.logical_and(in_nozzle_region, np.abs(Y_grid) >= y_bell - 0.06)
    nozzle_exterior = np.logical_and(in_nozzle_region, np.abs(Y_grid) >= y_bell + 0.04)
    nozzle_throat_glow = np.logical_and(in_nozzle_region, np.abs(Y_grid) < y_bell - 0.06)

    # Anodized titanium nozzle exterior shading
    nozzle_shading = 0.5 + 0.5 * np.sin(Y_grid * 12.0 + dx_nozzle * 8.0)
    R_total = np.where(nozzle_metal_wall, 45.0 + 35.0 * nozzle_shading, R_total)
    G_total = np.where(nozzle_metal_wall, 52.0 + 40.0 * nozzle_shading, G_total)
    B_total = np.where(nozzle_metal_wall, 75.0 + 55.0 * nozzle_shading, B_total)

    R_total = np.where(nozzle_exterior, 12.0, R_total)
    G_total = np.where(nozzle_exterior, 14.0, G_total)
    B_total = np.where(nozzle_exterior, 20.0, B_total)

    # Incandescent combustion chamber glow deep inside the nozzle throat
    throat_dist = np.maximum(0.0, -dx_nozzle) / 1.2
    throat_glow = np.exp(-throat_dist * 2.2) * (1.0 - (np.abs(Y_grid) / (y_bell + 1e-4))**2)
    R_total = np.where(nozzle_throat_glow, np.clip(R_total + throat_glow * 255.0, 0, 255), R_total)
    G_total = np.where(nozzle_throat_glow, np.clip(G_total + throat_glow * 210.0, 0, 255), G_total)
    B_total = np.where(nozzle_throat_glow, np.clip(B_total + throat_glow * 110.0, 0, 255), B_total)

    # Nozzle lip glowing hot rim
    lip_mask = np.logical_and(np.abs(dx_nozzle) < 0.04, np.abs(np.abs(Y_grid) - 0.42) < 0.06)
    R_total = np.where(lip_mask, 255.0, R_total)
    G_total = np.where(lip_mask, 190.0, G_total)
    B_total = np.where(lip_mask, 80.0, B_total)

    # Soft cinematic vignette around canvas borders
    vig_x = np.clip(1.0 - (X_grid / 4.4)**4, 0.0, 1.0)
    vig_y = np.clip(1.0 - (Y_grid / (4.4 * (Ny / Nx)))**4, 0.0, 1.0)
    vignette = np.sqrt(vig_x * vig_y)

    # Populate ARGB buffer
    pixel_buffer[..., 0] = 255
    pixel_buffer[..., 1] = (R_total * vignette).astype(np.uint8)
    pixel_buffer[..., 2] = (G_total * vignette).astype(np.uint8)
    pixel_buffer[..., 3] = (B_total * vignette).astype(np.uint8)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(3, 7, 18)


def draw_frame():
    global particles

    # 1. Physics field computation
    (
        core_mask,
        core_axial_stream,
        diamond_shocks,
        mach_disks,
        post_shock_heat,
        slip_lines,
        expansion_field,
        kh_streamlines,
        schlieren_norm,
        u_axial,
        v_radial,
        R_jet,
        nozzle_exit_x,
    ) = compute_supersonic_flow_fields(py5.frame_count)

    # 2. Render base field to pixel buffer
    render_supersonic_canvas(
        core_mask,
        core_axial_stream,
        diamond_shocks,
        mach_disks,
        post_shock_heat,
        slip_lines,
        expansion_field,
        kh_streamlines,
        schlieren_norm,
        nozzle_exit_x,
        py5.frame_count,
    )

    # 3. Blit upscaled pixel buffer to 4K canvas
    img = py5.create_image(Nx, Ny, py5.ARGB)
    img.load_np_pixels()
    if img.np_pixels is not None:
        img.np_pixels[:] = pixel_buffer
        img.update_np_pixels()
    else:
        a = pixel_buffer[..., 0].astype(np.int32)
        r = pixel_buffer[..., 1].astype(np.int32)
        g = pixel_buffer[..., 2].astype(np.int32)
        b = pixel_buffer[..., 3].astype(np.int32)
        img.pixels[:] = (a << 24) | (r << 16) | (g << 8) | b
        img.update_pixels()

    py5.image(img, 0, 0, py5.width, py5.height)

    # 4. Lagrangian Supersonic Plasma Spark Spawning
    nozzle_canvas_x = ((nozzle_exit_x - x_coords[0]) / (x_coords[-1] - x_coords[0])) * py5.width
    canvas_center_y = py5.height / 2.0
    r0_canvas = (0.42 / (y_coords[-1] - y_coords[0])) * py5.height

    if len(particles) < MAX_PARTICLES:
        spawn_n = min(45, MAX_PARTICLES - len(particles))
        for _ in range(spawn_n):
            is_core = random.random() < 0.65
            if is_core:
                # Core sparks: spawn at nozzle throat and across first 2 shock cells
                py = canvas_center_y + random.uniform(-0.85, 0.85) * r0_canvas
                px = nozzle_canvas_x + random.uniform(-20, 220)
                particles.append(PlasmaParticle(px, py, is_core=True))
            else:
                # Shear boundary sparks: spawn along undulating boundary
                sign = 1.0 if random.random() < 0.5 else -1.0
                py = canvas_center_y + sign * r0_canvas * random.uniform(0.85, 1.35)
                px = nozzle_canvas_x + random.uniform(20, 350)
                particles.append(PlasmaParticle(px, py, is_core=False))

    # 5. Advect and Render Lagrangian Supersonic Plasma Sparks
    py5.blend_mode(py5.ADD)
    active_particles = []

    for p in particles:
        # Sample velocity and shock boost from grid
        gx = int(np.clip(((p.px / py5.width) * (Nx - 1)), 0, Nx - 1))
        gy = int(np.clip(((p.py / py5.height) * (Ny - 1)), 0, Ny - 1))

        flow_vx = float(u_axial[gy, gx]) * 4.2
        flow_vy = float(v_radial[gy, gx]) * 4.2
        shock_boost = float(mach_disks[gy, gx] * 1.5 + diamond_shocks[gy, gx] * 0.8)

        p.update(flow_vx, flow_vy, shock_boost)

        if not p.is_dead:
            active_particles.append(p)

            # Spark color: shifts from incandescent gold/white to electric cyan and deep indigo
            life_norm = p.life / p.max_life
            alpha = int(255 * (life_norm if life_norm < 0.8 else (1.0 - life_norm) * 5.0))

            if p.temp > 0.6:
                # Incandescent solar white-gold spark
                cr = 255
                cg = int(220 + 35 * p.temp)
                cb = int(140 * (1.0 - p.temp) + 240 * p.temp)
            else:
                # Ionized electric cyan spark
                cr = int(20 + 120 * p.temp)
                cg = int(180 + 75 * p.temp)
                cb = 255

            # Outer glow halo
            py5.no_stroke()
            py5.fill(cr, cg, cb, int(alpha * 0.22))
            py5.circle(p.px, p.py, p.radius * 3.2)

            # Core nucleus
            py5.fill(255, 255, 245, alpha)
            py5.circle(p.px, p.py, p.radius * 0.95)

            # High-velocity supersonic streak line
            py5.stroke(cr, cg, cb, int(alpha * 0.65))
            py5.stroke_weight(1.4)
            py5.line(p.px, p.py, p.prev_x, p.prev_y)

    particles = active_particles
    py5.blend_mode(py5.BLEND)

    # 6. Safety check: fail-safe blank screen detection
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # 7. Save animation frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        progress_pct = (py5.frame_count / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Sparks: {len(particles)}")

    # 8. Finalize render on completion
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()

        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        mp4_path = SKETCH_DIR / f"{WORK_NAME}.mp4"
        output_mp4 = SKETCH_DIR / "output.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18", str(mp4_path),
        ], check=True)
        shutil.copyfile(mp4_path, output_mp4)

        # Save preview snapshot from midpoint
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

        # Clean up temporary frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")

        import os
        os._exit(0)


def draw():
    try:
        draw_frame()
    except Exception:
        import traceback
        traceback.print_exc()
        import os
        os._exit(1)


py5.run_sketch()

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
Nx, Ny = 640, 360
x_coords = np.linspace(-5.0, 5.0, Nx, dtype=np.float32)
y_coords = np.linspace(-5.0 * (Ny / Nx), 5.0 * (Ny / Nx), Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)

R2_grid = X_grid**2 + Y_grid**2
R_grid = np.sqrt(R2_grid) + 1e-5
Theta_grid = np.arctan2(Y_grid, X_grid)

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Lagrangian Micro-Droplet and Vortex Spark Tracers
MAX_DROPLETS = 900
droplet_particles = []


class LiquidDroplet:
    def __init__(self, px, py, initial_speed, angle):
        self.px = px
        self.py = py
        self.prev_x = px
        self.prev_y = py
        self.vx = np.cos(angle) * initial_speed
        self.vy = np.sin(angle) * initial_speed
        self.life = random.uniform(70.0, 190.0)
        self.max_life = self.life
        self.radius = random.uniform(1.8, 3.8)
        self.is_trapped = False

    def update(self, vr_flow, vtheta_flow, local_jump_prox):
        self.prev_x = self.px
        self.prev_y = self.py

        # Convert flow from polar to Cartesian coordinates
        center_x = py5.width / 2.0
        center_y = py5.height / 2.0
        dx = self.px - center_x
        dy = self.py - center_y
        dist = np.sqrt(dx**2 + dy**2) + 1e-5
        cos_t = dx / dist
        sin_t = dy / dist

        # Target flow velocity in cartesian
        target_vx = vr_flow * cos_t - vtheta_flow * sin_t
        target_vy = vr_flow * sin_t + vtheta_flow * cos_t

        # Droplet inertia
        drag = 0.88 if local_jump_prox > 0.4 else 0.94
        blend = 0.22 if local_jump_prox > 0.4 else 0.12

        jitter_x = random.uniform(-0.12, 0.12)
        jitter_y = random.uniform(-0.12, 0.12)

        self.vx = self.vx * drag + (target_vx + jitter_x) * blend
        self.vy = self.vy * drag + (target_vy + jitter_y) * blend

        self.px += self.vx
        self.py += self.vy

        if self.px < 0 or self.px >= py5.width or self.py < 0 or self.py >= py5.height:
            self.life = 0

        self.life -= 1.0

    @property
    def is_dead(self):
        return self.life <= 0


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def compute_hydraulic_jump_field(frame_idx):
    # Normalized time tau in [0, 2*pi] over TOTAL_FRAMES for seamless loop
    tau = (2.0 * np.pi * frame_idx) / TOTAL_FRAMES

    # Flow rate modulation (smooth periodic breathing)
    q_mod = 1.0 + 0.18 * np.sin(tau)

    # Base jump radius
    R0 = 2.15 * q_mod

    # Polygonal instability mode amplitudes and rotations
    # Seamless integer frequency multipliers:
    # Mode 3 (triangle), Mode 4 (square), Mode 5 (pentagon), Mode 6 (hexagon)
    a3 = 0.18 * (0.5 + 0.5 * np.cos(tau))
    a4 = 0.24 * (0.5 + 0.5 * np.sin(tau + 0.5 * np.pi))
    a5 = 0.20 * (0.5 + 0.5 * np.sin(tau + 1.2 * np.pi))
    a6 = 0.12 * (0.5 + 0.5 * np.cos(tau + 1.6 * np.pi))

    # Mode rotation speeds (synchronized to tau)
    theta3 = Theta_grid - 1.0 * tau
    theta4 = Theta_grid + 1.0 * tau
    theta5 = Theta_grid - 2.0 * tau
    theta6 = Theta_grid + 1.0 * tau

    # Polygonal radius boundary R_jump(theta, t)
    R_jump = R0 * (
        1.0
        + a3 * np.cos(3.0 * theta3)
        + a4 * np.cos(4.0 * theta4)
        + a5 * np.cos(5.0 * theta5)
        + a6 * np.cos(6.0 * theta6)
    )

    # Normalized radial distance relative to jump boundary
    # xi < 0: supercritical thin sheet, xi > 0: subcritical deep pool
    xi = R_grid - R_jump

    # Supercritical inner thin-film height h1(r)
    # Thin film spreading: h ~ h0 / r, with central impingement mound
    h_jet = 0.65 * np.exp(- (R_grid / 0.42)**2)
    h_film = 0.14 * (0.75 / (R_grid + 0.25))

    # Subcritical outer pool height h2 with capillary ripples
    # Capillary ripple frequency and decay
    ripple_phase = 14.0 * xi - 3.0 * tau
    capillary_waves = 0.045 * np.exp(- np.maximum(xi, 0.0) / 1.1) * np.cos(ripple_phase)

    # Abrupt hydraulic shockfront profile using tanh transition
    shock_width = 0.08
    jump_transition = 0.5 * (1.0 + np.tanh(xi / shock_width))

    # Total liquid surface height h(x, y)
    h_inner = h_jet + h_film
    h_outer = 0.48 + capillary_waves
    h_surface = (1.0 - jump_transition) * h_inner + jump_transition * h_outer

    # Shockfront ridge intensity (sharp crest at xi approx 0)
    shock_ridge = np.exp(- (xi / 0.09)**2)

    # Corner roller vortex recirculation:
    # Corners are local maxima of R_jump where curvature and separation occur
    # Compute azimuthal derivative of R_jump to locate corners
    d_theta = 0.01
    R_jump_plus = R0 * (
        1.0
        + a3 * np.cos(3.0 * (theta3 + d_theta))
        + a4 * np.cos(4.0 * (theta4 + d_theta))
        + a5 * np.cos(5.0 * (theta5 + d_theta))
        + a6 * np.cos(6.0 * (theta6 + d_theta))
    )
    d_theta_jump = (R_jump_plus - R_jump) / d_theta
    vortex_intensity = shock_ridge * np.abs(d_theta_jump) * 2.8

    # Velocity fields for particle advection:
    # 1. Radial velocity: ultrafast in supercritical, decelerates 5x across jump
    vr = np.where(
        xi < 0,
        14.0 / (R_grid + 0.35),
        2.2 / (R_grid + 0.1) * np.exp(- np.maximum(xi, 0.0) / 1.8)
    )

    # 2. Azimuthal vortex circulation at corners
    vtheta = vortex_intensity * 4.5 * np.sign(d_theta_jump)

    # Surface normal gradient for Blinn-Phong specular liquid rendering
    dh_dy = np.gradient(h_surface, axis=0) * (Ny / 4.8)
    dh_dx = np.gradient(h_surface, axis=1) * (Nx / 4.8)

    # Normals: N = (-dh/dx, -dh/dy, 1) normalized
    norm_len = np.sqrt(dh_dx**2 + dh_dy**2 + 1.0)
    nx = -dh_dx / norm_len
    ny = -dh_dy / norm_len
    nz = 1.0 / norm_len

    # Dual light source specular reflections:
    # Light 1 (Electric Cyan Key Light from top-left: [-0.45, -0.45, 0.77])
    lx1, ly1, lz1 = -0.45, -0.45, 0.77
    h1x, h1y, h1z = lx1, ly1, lz1 + 1.0
    h1_len = np.sqrt(h1x**2 + h1y**2 + h1z**2)
    h1x, h1y, h1z = h1x / h1_len, h1y / h1_len, h1z / h1_len
    spec1 = np.maximum(0.0, nx * h1x + ny * h1y + nz * h1z)**28

    # Light 2 (Incandescent Amber/Gold Rim Light from bottom-right: [0.55, 0.55, 0.63])
    lx2, ly2, lz2 = 0.55, 0.55, 0.63
    h2x, h2y, h2z = lx2, ly2, lz2 + 1.0
    h2_len = np.sqrt(h2x**2 + h2y**2 + h2z**2)
    h2x, h2y, h2z = h2x / h2_len, h2y / h2_len, h2z / h2_len
    spec2 = np.maximum(0.0, nx * h2x + ny * h2y + nz * h2z)**36

    # Radial vignette to protect edges
    vignette = np.exp(- (R_grid / 4.5)**6)

    return (
        h_surface, shock_ridge, vortex_intensity,
        spec1, spec2, vignette,
        vr, vtheta, xi
    )


def render_hydraulic_jump_canvas(h_surface, shock_ridge, vortex_intensity, spec1, spec2, vignette):
    # Palette Construction:
    # 1. 60% Matrix: Abyssal Hydrodynamic Obsidian (#02060d) & Vitreous Cobalt (#0a1f44)
    r = np.full_like(X_grid, 2.0)
    g = np.full_like(X_grid, 6.0)
    b = np.full_like(X_grid, 13.0)

    # Liquid depth modulation
    h_norm = np.clip(h_surface / 0.85, 0.0, 1.0)
    r += h_norm * 14.0 * vignette
    g += h_norm * 45.0 * vignette
    b += h_norm * 110.0 * vignette

    # 2. 30% Bioluminescent Liquid Cyan & Aquamarine (#00f0ff, #0ae8b0)
    # Shockfront crest and capillary ripples
    cyan_glow = shock_ridge * vignette
    r += cyan_glow * 10.0
    g += cyan_glow * 230.0
    b += cyan_glow * 255.0

    # Key light specular highlight (Luminous Cyan / Jade Sheen)
    r += spec1 * vignette * 50.0
    g += spec1 * vignette * 240.0
    b += spec1 * vignette * 255.0

    # 3. 10% Incandescent Solar Gold & Foam White (#ffe680, #ffffff)
    # Corner recirculation vortices
    vortex_glow = vortex_intensity * vignette
    r += vortex_glow * 255.0
    g += vortex_glow * 215.0
    b += vortex_glow * 90.0

    # Rim light specular highlight (Solar Gold)
    r += spec2 * vignette * 255.0
    g += spec2 * vignette * 220.0
    b += spec2 * vignette * 120.0

    # Central impingement stagnation spot (pure incandescence)
    center_glow = np.exp(- (R_grid / 0.32)**2)
    r += center_glow * 255.0
    g += center_glow * 250.0
    b += center_glow * 230.0

    # Populate ARGB pixel buffer
    pixel_buffer[..., 0] = 255
    pixel_buffer[..., 1] = np.clip(r, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b, 0, 255).astype(np.uint8)


def draw_frame():
    global droplet_particles

    # 1. Physics field computation
    (h_surface, shock_ridge, vortex_intensity,
     spec1, spec2, vignette,
     vr_flow, vtheta_flow, xi) = compute_hydraulic_jump_field(py5.frame_count)

    # 2. Render pixel buffer
    render_hydraulic_jump_canvas(h_surface, shock_ridge, vortex_intensity, spec1, spec2, vignette)

    # 3. Blit upscaled to 4K canvas
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

    # 4. Lagrangian Droplet particle emission at central impingement jet
    center_px = py5.width / 2.0
    center_py = py5.height / 2.0

    if len(droplet_particles) < MAX_DROPLETS:
        spawn_n = min(35, MAX_DROPLETS - len(droplet_particles))
        for _ in range(spawn_n):
            angle = random.uniform(0.0, 2.0 * np.pi)
            init_r = random.uniform(2.0, 18.0)
            px = center_px + np.cos(angle) * init_r
            py = center_py + np.sin(angle) * init_r
            speed = random.uniform(14.0, 22.0)
            droplet_particles.append(LiquidDroplet(px, py, speed, angle))

    # 5. Advect and render droplet tracers in ADD blend mode
    py5.blend_mode(py5.ADD)
    active_droplets = []

    for d in droplet_particles:
        gx = int(np.clip((d.px / py5.width) * (Nx - 1), 0, Nx - 1))
        gy = int(np.clip((d.py / py5.height) * (Ny - 1), 0, Ny - 1))

        local_vr = vr_flow[gy, gx]
        local_vtheta = vtheta_flow[gy, gx]
        local_ridge = shock_ridge[gy, gx]
        local_vortex = vortex_intensity[gy, gx]

        d.update(local_vr, local_vtheta, local_ridge)

        if not d.is_dead:
            active_droplets.append(d)
            life_norm = d.life / d.max_life
            alpha = int(life_norm * (160 + local_ridge * 95))

            # Color shift: Electric Cyan in thin sheet -> Solar Gold in corner eddies
            if local_vortex > 0.35:
                cr = 255
                cg = int(220 + life_norm * 35)
                cb = int(110 + life_norm * 80)
            elif local_ridge > 0.30:
                cr = 240
                cg = 255
                cb = 255
            else:
                cr = int(30 + life_norm * 50)
                cg = int(235 + life_norm * 20)
                cb = int(250 + life_norm * 5)

            # Droplet aura glow
            py5.no_stroke()
            py5.fill(cr, cg, cb, int(alpha * 0.36))
            py5.circle(d.px, d.py, d.radius * 2.6)

            # Droplet core
            py5.fill(255, 255, 250, alpha)
            py5.circle(d.px, d.py, d.radius * 0.95)

            # Fast streak filament
            py5.stroke(cr, cg, cb, int(alpha * 0.55))
            py5.stroke_weight(1.2)
            py5.line(d.px, d.py, d.prev_x, d.prev_y)

    droplet_particles = active_droplets
    py5.blend_mode(py5.BLEND)

    # Fail-safe blank screen check
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Save animation frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        progress_pct = (py5.frame_count / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Active Droplets: {len(droplet_particles)}")

    # Finalize render
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

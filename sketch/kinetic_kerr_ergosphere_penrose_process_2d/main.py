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
x_coords = np.linspace(-4.6, 4.6, Nx, dtype=np.float32)
y_coords = np.linspace(-4.6 * (Ny / Nx), 4.6 * (Ny / Nx), Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)

R2_grid = X_grid**2 + Y_grid**2
R_grid = np.sqrt(R2_grid) + 1e-5
Theta_grid = np.arctan2(Y_grid, X_grid)

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Lagrangian Penrose Particle Kinematics
MAX_PARTICLES = 1000
penrose_particles = []


class PenroseSpark:
    def __init__(self, px, py, is_penrose_ejected=False):
        self.px = px
        self.py = py
        self.prev_x = px
        self.prev_y = py
        self.vx = 0.0
        self.vy = 0.0
        self.is_ejected = is_penrose_ejected
        self.life = random.uniform(50.0, 160.0) if not is_penrose_ejected else random.uniform(90.0, 210.0)
        self.max_life = self.life
        self.radius = random.uniform(1.8, 3.8) if is_penrose_ejected else random.uniform(1.2, 2.4)
        self.has_split = is_penrose_ejected

    def update(self, vr_flow, vtheta_flow, in_ergosphere, horizon_radius):
        self.prev_x = self.px
        self.prev_y = self.py

        center_x = py5.width / 2.0
        center_y = py5.height / 2.0
        dx = self.px - center_x
        dy = self.py - center_y
        dist = np.sqrt(dx**2 + dy**2) + 1e-5
        cos_t = dx / dist
        sin_t = dy / dist

        # Velocity in cartesian coordinates
        target_vx = vr_flow * cos_t - vtheta_flow * sin_t
        target_vy = vr_flow * sin_t + vtheta_flow * cos_t

        if self.is_ejected:
            # Ejected high-energy particle racing outward with relativistic boost
            boost = 3.8
            self.vx = self.vx * 0.94 + target_vx * boost * 0.18
            self.vy = self.vy * 0.94 + target_vy * boost * 0.18
        else:
            self.vx = self.vx * 0.88 + target_vx * 0.22
            self.vy = self.vy * 0.88 + target_vy * 0.22

        self.px += self.vx
        self.py += self.vy

        # Check if crossed event horizon (disappear into singularity)
        dist_grid = (dist / (py5.width * 0.5)) * 4.6
        if dist_grid < horizon_radius:
            self.life = 0

        # Screen boundaries
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


def compute_kerr_spacetime(frame_idx):
    # Normalized time tau in [0, 2*pi] over TOTAL_FRAMES
    tau = (2.0 * np.pi * frame_idx) / TOTAL_FRAMES

    # Kerr Black Hole Parameters
    M = 1.0
    a_spin = 0.94  # Near-extremal Kerr spin

    # Event Horizon Radius r+
    r_plus = M + np.sqrt(M**2 - a_spin**2)  # approx 1.34

    # Ergosphere Static Limit r_E(theta)
    # Inclined view: polar angle relative to spin axis
    cos_theta_spin = np.cos(Theta_grid + 0.35 * np.pi)
    r_ergo = M + np.sqrt(np.maximum(0.01, M**2 - (a_spin * cos_theta_spin)**2))

    # Lense-Thirring frame dragging angular velocity omega_LT(r)
    omega_LT = (2.0 * M * a_spin * R_grid) / (R_grid**4 + a_spin**2 * R_grid**2 + 2.0 * M * a_spin**2 * R_grid + 0.1)

    # Infall velocity + frame dragging flow
    # Inside ergosphere, matter is dragged faster than light
    vr_flow = - (1.6 / (R_grid + 0.2)) * (1.0 + 0.15 * np.sin(3.0 * Theta_grid - tau))
    vtheta_flow = omega_LT * 3.6

    # Relativistic Doppler Beaming factor:
    # Matter approaching observer on left (dx < 0, dy > 0 depending on rotation direction)
    beta = np.clip(omega_LT * 0.85, 0.0, 0.88)
    gamma = 1.0 / np.sqrt(1.0 - beta**2 + 1e-5)
    # Line of sight projection
    cos_los = np.sin(Theta_grid)
    doppler_factor = 1.0 / (gamma * (1.0 - beta * cos_los) + 1e-4)

    # Gravitational Redshift factor: sqrt(1 - 2M/r)
    redshift = np.sqrt(np.maximum(0.02, 1.0 - (2.0 * M) / (R_grid + 0.1)))
    combined_spectral_shift = doppler_factor * redshift

    # Spacetime Geodesic Spiral Ribbons:
    # Infalling logarithmic spirals twisted by frame-dragging
    spiral_phase = 4.0 * np.log(R_grid + 0.2) - 3.0 * Theta_grid + 2.0 * tau
    spiral_ribbons = np.exp(- ((np.sin(spiral_phase * 0.5)) / 0.18)**2)

    # Ergosphere static limit contour ring (halo)
    ergo_contour = np.exp(- ((R_grid - r_ergo) / 0.08)**2)

    # Event Horizon boundary (shadow edge)
    horizon_shadow = 0.5 * (1.0 + np.tanh((R_grid - r_plus) / 0.04))

    # Photon sphere peak glow (r_ph approx 1.6 M)
    photon_ring = np.exp(- ((R_grid - 1.55) / 0.06)**2)

    # Relativistic Jet Emission along spin axis (Penrose process extraction)
    # Spin axis at angle theta_jet = 0.35*pi and 1.35*pi
    jet_angle1 = 0.35 * np.pi
    jet_angle2 = 1.35 * np.pi
    d_angle1 = np.abs(np.arctan2(np.sin(Theta_grid - jet_angle1), np.cos(Theta_grid - jet_angle1)))
    d_angle2 = np.abs(np.arctan2(np.sin(Theta_grid - jet_angle2), np.cos(Theta_grid - jet_angle2)))
    jet_collimation = (np.exp(- (d_angle1 / 0.16)**2) + np.exp(- (d_angle2 / 0.16)**2)) * (R_grid > r_plus) * np.exp(- (R_grid / 4.2))

    # Outer vignette
    vignette = np.exp(- (R_grid / 4.5)**6)

    return (
        R_grid, r_plus, r_ergo,
        horizon_shadow, ergo_contour, photon_ring,
        spiral_ribbons, combined_spectral_shift, jet_collimation,
        vignette, vr_flow, vtheta_flow
    )


def render_kerr_canvas(R_grid, r_plus, r_ergo,
                       horizon_shadow, ergo_contour, photon_ring,
                       spiral_ribbons, spectral_shift, jet_collimation, vignette):
    # Palette Architecture:
    # 1. 60% Matrix: Event Horizon Singularity Obsidian (#010206) & Gravitationally Redshifted Crimson/Violet (#4c0519, #2e1065)
    r = np.full_like(X_grid, 1.0)
    g = np.full_like(X_grid, 2.0)
    b = np.full_like(X_grid, 6.0)

    # Infalling accretion disk ambient glow
    disk_intensity = (1.0 / (R_grid + 0.6)) * horizon_shadow * vignette

    # Redshifted receding flank (Crimson / Deep Amethyst)
    redshift_weight = np.clip((1.2 - spectral_shift), 0.0, 1.0) * disk_intensity
    r += redshift_weight * 140.0
    g += redshift_weight * 10.0
    b += redshift_weight * 70.0

    # 2. 30% Relativistically Blueshifted Cyan & Celestial Mint (#06b6d4, #10b981)
    blueshift_weight = np.clip((spectral_shift - 0.9), 0.0, 2.5) * disk_intensity
    r += blueshift_weight * 20.0
    g += blueshift_weight * 210.0
    b += blueshift_weight * 255.0

    # Geodesic spiral ribbons
    spiral_glow = spiral_ribbons * disk_intensity * 1.8
    r += spiral_glow * (30.0 + blueshift_weight * 40.0)
    g += spiral_glow * (160.0 + blueshift_weight * 80.0)
    b += spiral_glow * (240.0 + blueshift_weight * 15.0)

    # Ergosphere Static Limit Ring (Luminescent Electric Cyan & Violet)
    ergo_glow = ergo_contour * vignette
    r += ergo_glow * 160.0
    g += ergo_glow * 220.0
    b += ergo_glow * 255.0

    # 3. 10% Incandescent Penrose Beaming Gold & Pure White (#fef08a, #ffffff)
    # Photon sphere ring (pure incandescent light)
    photon_glow = photon_ring * vignette * (1.0 + blueshift_weight * 1.2)
    r += photon_glow * 255.0
    g += photon_glow * 245.0
    b += photon_glow * 200.0

    # Relativistic Penrose Jet beams
    jet_glow = jet_collimation * vignette * 2.2
    r += jet_glow * 255.0
    g += jet_glow * 225.0
    b += jet_glow * 110.0

    # Absolute Event Horizon Black Hole Void (strict zero within r_plus)
    horizon_mask = 0.5 * (1.0 + np.tanh((R_grid - (r_plus - 0.05)) / 0.03))
    r *= horizon_mask
    g *= horizon_mask
    b *= horizon_mask

    # Populate ARGB pixel buffer
    pixel_buffer[..., 0] = 255
    pixel_buffer[..., 1] = np.clip(r, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b, 0, 255).astype(np.uint8)


def draw_frame():
    global penrose_particles

    # 1. Physics field computation
    (R_grid, r_plus, r_ergo,
     horizon_shadow, ergo_contour, photon_ring,
     spiral_ribbons, spectral_shift, jet_collimation,
     vignette, vr_flow, vtheta_flow) = compute_kerr_spacetime(py5.frame_count)

    # 2. Render pixel buffer
    render_kerr_canvas(R_grid, r_plus, r_ergo,
                       horizon_shadow, ergo_contour, photon_ring,
                       spiral_ribbons, spectral_shift, jet_collimation, vignette)

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

    # 4. Infall and Penrose Particle Spawning
    center_px = py5.width / 2.0
    center_py = py5.height / 2.0

    if len(penrose_particles) < MAX_PARTICLES:
        spawn_n = min(35, MAX_PARTICLES - len(penrose_particles))
        for _ in range(spawn_n):
            angle = random.uniform(0.0, 2.0 * np.pi)
            init_r = random.uniform(0.35, 0.95) * (py5.height * 0.48)
            px = center_px + np.cos(angle) * init_r * 1.6
            py = center_py + np.sin(angle) * init_r
            penrose_particles.append(PenroseSpark(px, py, is_penrose_ejected=False))

    # 5. Advect and split particles via Penrose process
    py5.blend_mode(py5.ADD)
    active_sparks = []
    spawned_ejected = []

    for p in penrose_particles:
        gx = int(np.clip((p.px / py5.width) * (Nx - 1), 0, Nx - 1))
        gy = int(np.clip((p.py / py5.height) * (Ny - 1), 0, Ny - 1))

        local_vr = vr_flow[gy, gx]
        local_vtheta = vtheta_flow[gy, gx]
        local_r = R_grid[gy, gx]
        local_ergo = r_ergo[gy, gx]
        in_ergo = (local_r < local_ergo) and (local_r > r_plus)

        # Penrose fission: if inside ergosphere and haven't split yet
        if in_ergo and not p.has_split and random.random() < 0.08 and len(penrose_particles) < MAX_PARTICLES:
            p.has_split = True
            # Spawn daughter particle launched into relativistic escape trajectory
            spawned_ejected.append(PenroseSpark(p.px, p.py, is_penrose_ejected=True))

        p.update(local_vr, local_vtheta, in_ergo, r_plus)

        if not p.is_dead:
            active_sparks.append(p)
            life_norm = p.life / p.max_life
            alpha = int(life_norm * 220)

            if p.is_ejected:
                # Ejected Penrose energy spark: Incandescent Solar Gold
                cr = 255
                cg = int(230 + life_norm * 25)
                cb = int(120 + life_norm * 90)
            elif in_ergo:
                # Inside ergosphere: Ionizing Cyan / Mint Jade
                cr = int(30 + life_norm * 60)
                cg = int(240 + life_norm * 15)
                cb = int(220 + life_norm * 35)
            else:
                # Outer infalling: Deep Violet / Amethyst
                cr = int(140 + life_norm * 60)
                cg = int(40 + life_norm * 70)
                cb = 240

            # Aura
            py5.no_stroke()
            py5.fill(cr, cg, cb, int(alpha * 0.38))
            py5.circle(p.px, p.py, p.radius * 2.8)

            # Nucleus
            py5.fill(255, 255, 245, alpha)
            py5.circle(p.px, p.py, p.radius * 0.95)

            # Relativistic streak filament
            py5.stroke(cr, cg, cb, int(alpha * 0.55))
            py5.stroke_weight(1.3)
            py5.line(p.px, p.py, p.prev_x, p.prev_y)

    active_sparks.extend(spawned_ejected)
    penrose_particles = active_sparks
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
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Active Sparks: {len(penrose_particles)}")

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

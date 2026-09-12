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
# Co-moving frame coordinates: Xi (horizontal, laser moves right) and Y (transverse)
Nx, Ny = 640, 360
xi_coords = np.linspace(-3.8, 3.8, Nx, dtype=np.float32)
y_coords = np.linspace(-3.8 * (Ny / Nx), 3.8 * (Ny / Nx), Ny, dtype=np.float32)
Xi_grid, Y_grid = np.meshgrid(xi_coords, y_coords)

# Distance from primary bubble center (Xi_c = 0.55)
XI_C = 0.55
R2_grid = (Xi_grid - XI_C)**2 + Y_grid**2
R_grid = np.sqrt(R2_grid) + 1e-5

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Lagrangian Relativistic Witness & Sheath Particles
MAX_PARTICLES = 1300
particles = []


class RelativisticElectron:
    def __init__(self, px, py, is_witness=False):
        self.px = px
        self.py = py
        self.prev_x = px
        self.prev_y = py
        self.vx = 0.0
        self.vy = 0.0
        self.is_witness = is_witness
        self.energy = random.uniform(8.0, 45.0) if is_witness else random.uniform(1.0, 4.0)
        self.betatron_phase = random.uniform(0.0, 2.0 * np.pi)
        self.life = random.uniform(90.0, 260.0) if is_witness else random.uniform(60.0, 180.0)
        self.max_life = self.life
        self.radius = random.uniform(1.6, 3.4) if is_witness else random.uniform(1.0, 2.2)

    def update(self, Ez_accel, Fr_focus, flow_vx, flow_vy, dt=1.0):
        self.prev_x = self.px
        self.prev_y = self.py

        if self.is_witness:
            # Trapped witness electrons accelerating to multi-GeV energies
            self.energy += max(0.0, Ez_accel * 0.85)
            # Betatron oscillation: high-frequency serpentine transverse motion
            betatron_freq = 0.28 / (np.sqrt(self.energy) + 0.1)
            self.betatron_phase += betatron_freq * dt
            betatron_force = -0.45 * np.sin(self.betatron_phase) * np.exp(-abs(self.py - py5.height / 2.0) * 0.01)

            target_vx = (flow_vx * 1.5 + 4.8)
            target_vy = flow_vy * 0.6 + Fr_focus * 1.8 + betatron_force * 3.5

            self.vx = self.vx * 0.85 + target_vx * 0.15
            self.vy = self.vy * 0.82 + target_vy * 0.18
        else:
            # Sheath electrons sweeping around bubble boundary toward rear cusp
            target_vx = flow_vx * 1.2
            target_vy = flow_vy * 1.4 + Fr_focus * 0.8
            self.vx = self.vx * 0.88 + target_vx * 0.12
            self.vy = self.vy * 0.88 + target_vy * 0.12

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


def compute_wakefield_bubble_fields(frame):
    """
    Computes relativistic plasma wakefield acceleration in the blowout/bubble regime:
    - Ponderomotive electron cavitation (spherical ion bubble)
    - High-density relativistic electron sheath
    - Multi-GV/m longitudinal accelerating field (Ez)
    - Linear transverse focusing field (Er - c*Btheta)
    - Trailing secondary and tertiary plasma wave cavities
    - Relativistic drive laser pulse front
    """
    t = frame / 60.0  # seconds

    # Laser pulse parameters
    laser_speed = 0.06
    laser_w0 = 0.32
    laser_xi = 2.45 + 0.03 * np.sin(4.0 * np.pi * t)
    laser_pulse = np.exp(- ((Xi_grid - laser_xi)**2) / (2.0 * (laser_w0**2)) - (Y_grid**2) / 0.12)
    laser_optical_cycles = np.cos(18.0 * (Xi_grid - laser_xi) - 24.0 * t)**2
    laser_intensity = laser_pulse * laser_optical_cycles

    # 1. Primary Bubble (Blowout Cavity) Geometry: Sleek Aerodynamic Teardrop Blowout
    R_b0 = 1.82
    dx_rel = (Xi_grid - XI_C) / R_b0
    # Aerodynamic teardrop elongation: smooth aerodynamic slope at front, narrowing gracefully into rear cusp
    teardrop_factor = 1.0 + 0.18 * dx_rel - 0.08 * (dx_rel**2)
    dy_bubble = Y_grid / (R_b0 * np.maximum(0.3, teardrop_factor))
    dist_bubble = np.sqrt(dx_rel**2 + dy_bubble**2)

    # Cavity interior: bare positive ion background
    inside_cavity = np.clip(1.0 - (dist_bubble / 1.01)**5.0, 0.0, 1.0)

    # Relativistic Electron Sheath: smooth, sleek relativistic shell with subtle organic ripples
    theta_pol = np.arctan2(Y_grid, Xi_grid - XI_C)
    organic_ripples = 0.012 * np.sin(6.0 * theta_pol + 4.0 * np.pi * t) + 0.008 * np.cos(10.0 * theta_pol - 2.0 * np.pi * t)
    sheath_thickness = 0.075 + 0.012 * np.cos(2.0 * theta_pol)
    sheath_dist = np.abs(dist_bubble - 1.0 + organic_ripples)
    sheath_density = np.exp(- (sheath_dist**2) / (2.0 * (sheath_thickness**2)))

    # Sheath pinching cusp at rear vertex
    rear_cusp_xi = XI_C - 0.96 * R_b0
    rear_pinch = np.exp(- ((Xi_grid - rear_cusp_xi)**2) / 0.065 - (Y_grid**2) / 0.032) * 2.6
    sheath_density_total = sheath_density + rear_pinch

    # 2. Secondary & Tertiary Trailing Wake Cavities
    xi_c2 = XI_C - 2.15 * R_b0
    R_b2 = 1.15
    dist_b2 = np.sqrt(((Xi_grid - xi_c2) / R_b2)**2 + (Y_grid / R_b2)**2)
    cavity_2 = np.clip(1.0 - (dist_b2 / 1.02)**4.0, 0.0, 1.0) * 0.65
    sheath_2 = np.exp(- ((dist_b2 - 1.0)**2) / 0.018) * 0.72

    xi_c3 = xi_c2 - 1.85 * R_b2
    R_b3 = 0.75
    dist_b3 = np.sqrt(((Xi_grid - xi_c3) / R_b3)**2 + (Y_grid / R_b3)**2)
    cavity_3 = np.clip(1.0 - (dist_b3 / 1.02)**4.0, 0.0, 1.0) * 0.35
    sheath_3 = np.exp(- ((dist_b3 - 1.0)**2) / 0.022) * 0.42

    # 3. Longitudinal Accelerating Electric Field Ez
    Ez_primary = np.where(
        inside_cavity > 0.08,
        - (Xi_grid - XI_C) / R_b0,
        0.0
    )
    Ez_accel_core = np.maximum(0.0, Ez_primary) * inside_cavity

    # 4. Transverse Focusing Field Fr = Er - c*Btheta
    Fr_focus = np.where(
        inside_cavity > 0.05,
        - Y_grid / (R_b0 + 1e-4),
        0.0
    )

    # 5. Trapped Witness Bunch Profile
    bunch_xi = XI_C - 0.72 * R_b0
    bunch_y_center = 0.14 * np.sin(8.0 * np.pi * t)
    witness_bunch = np.exp(- ((Xi_grid - bunch_xi)**2) / 0.045 - ((Y_grid - bunch_y_center)**2) / 0.016)

    # Synchrotron / Betatron X-ray Emission Cones (Continuous smooth exponential decay without step cuts)
    dx_synch = np.maximum(0.0, Xi_grid - bunch_xi)
    dy_synch = np.abs(Y_grid - bunch_y_center)
    beam_spread = 0.10 + 0.16 * dx_synch
    synchrotron_beam = (
        np.exp(- (dy_synch / beam_spread)**2)
        * np.exp(- 1.45 * dx_synch)
        * np.clip((Xi_grid - bunch_xi + 0.05) / 0.12, 0.0, 1.0)
    )

    # 6. Flow Velocity Field for Particle Kinematics
    # Relativistic sheath flow wraps around the bubble surface
    theta_bubble = np.arctan2(Y_grid, Xi_grid - XI_C)
    u_axial = np.where(
        dist_bubble < 1.05,
        1.8 + 2.4 * Ez_accel_core,
        0.8 - 0.6 * np.cos(theta_bubble) * np.exp(-sheath_dist * 2.0)
    )
    v_radial = np.where(
        dist_bubble < 1.05,
        Fr_focus * 1.5,
        - np.sin(theta_bubble) * 1.6 * np.exp(-sheath_dist * 2.5)
    )

    return (
        inside_cavity,
        sheath_density_total,
        cavity_2,
        sheath_2,
        cavity_3,
        sheath_3,
        Ez_accel_core,
        Fr_focus,
        witness_bunch,
        synchrotron_beam,
        laser_intensity,
        u_axial,
        v_radial,
        bunch_xi,
        bunch_y_center,
    )


def render_wakefield_canvas(
    inside_cavity,
    sheath_density_total,
    cavity_2,
    sheath_2,
    cavity_3,
    sheath_3,
    Ez_accel_core,
    witness_bunch,
    synchrotron_beam,
    laser_intensity,
    frame,
):
    """
    Renders 4-channel image into pixel_buffer using strict 60-30-10 palette rules:
    - 60% Abyssal Vacuum Obsidian & Ion Cavity Cobalt/Indigo (#010206, #081026, #141d36)
    - 30% Relativistic Electron Sheath Cyan & Ozone Electric Blue (#00f0ff, #38bdf8)
    - 10% Accelerated Witness Bunch White-Gold & Betatron Synchrotron Violet (#ffffff, #fef08a, #f59e0b, #e879f9)
    """
    # Background: Deep relativistic vacuum obsidian
    bg_r = 2.0 + 1.5 * np.cos(Xi_grid * 0.25)
    bg_g = 4.0 + 2.0 * np.cos(Xi_grid * 0.2)
    bg_b = 10.0 + 5.0 * np.sin(Xi_grid * 0.2)

    # Dominant 60%: Ion Cavity Cobalt & Plasma Wake Indigo
    # The bare ion channel glows with deep translucent cobalt/indigo
    cavity_total = inside_cavity * 0.85 + cavity_2 * 0.5 + cavity_3 * 0.25
    r_dom = bg_r + cavity_total * 10.0 + Ez_accel_core * 12.0
    g_dom = bg_g + cavity_total * 22.0 + Ez_accel_core * 28.0
    b_dom = bg_b + cavity_total * 65.0 + Ez_accel_core * 85.0

    # Secondary 30%: Relativistic Sheaths & Laser Ponderomotive Waves
    # Electric Cyan (#00f0ff) & Ozone Blue (#38bdf8)
    sheath_total = (
        sheath_density_total * 1.35
        + sheath_2 * 0.85
        + sheath_3 * 0.55
        + laser_intensity * 0.95
    )
    cyan_r = sheath_total * 8.0
    cyan_g = sheath_total * 205.0
    cyan_b = sheath_total * 255.0

    # Accent 10%: Accelerated Witness Bunch & Betatron Synchrotron Violet
    # Incandescent solar white-gold core (#ffffff, #fef08a, #f59e0b) with synchrotron violet emission
    bunch_intensity = witness_bunch * 2.2
    synch_intensity = synchrotron_beam * 1.4

    accent_r = bunch_intensity * 255.0 + synch_intensity * 220.0
    accent_g = bunch_intensity * 245.0 + synch_intensity * 90.0
    accent_b = bunch_intensity * 175.0 + synch_intensity * 255.0

    # Composite layers
    R_total = np.clip(r_dom + cyan_r + accent_r, 0.0, 255.0)
    G_total = np.clip(g_dom + cyan_g + accent_g, 0.0, 255.0)
    B_total = np.clip(b_dom + cyan_b + accent_b, 0.0, 255.0)

    # Soft cinematic vignette around borders
    vig_xi = np.clip(1.0 - (Xi_grid / 3.8)**4, 0.0, 1.0)
    vig_y = np.clip(1.0 - (Y_grid / (3.8 * (Ny / Nx)))**4, 0.0, 1.0)
    vignette = np.sqrt(vig_xi * vig_y)

    # Populate ARGB buffer
    pixel_buffer[..., 0] = 255
    pixel_buffer[..., 1] = (R_total * vignette).astype(np.uint8)
    pixel_buffer[..., 2] = (G_total * vignette).astype(np.uint8)
    pixel_buffer[..., 3] = (B_total * vignette).astype(np.uint8)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(2, 4, 10)


def draw_frame():
    global particles

    # 1. Physics field computation
    (
        inside_cavity,
        sheath_density_total,
        cavity_2,
        sheath_2,
        cavity_3,
        sheath_3,
        Ez_accel_core,
        Fr_focus,
        witness_bunch,
        synchrotron_beam,
        laser_intensity,
        u_axial,
        v_radial,
        bunch_xi,
        bunch_y_center,
    ) = compute_wakefield_bubble_fields(py5.frame_count)

    # 2. Render field into pixel buffer
    render_wakefield_canvas(
        inside_cavity,
        sheath_density_total,
        cavity_2,
        sheath_2,
        cavity_3,
        sheath_3,
        Ez_accel_core,
        witness_bunch,
        synchrotron_beam,
        laser_intensity,
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

    # 4. Lagrangian Relativistic Electron Spawning
    canvas_center_x = py5.width / 2.0
    canvas_center_y = py5.height / 2.0
    xi_scale = py5.width / (xi_coords[-1] - xi_coords[0])
    y_scale = py5.height / (y_coords[-1] - y_coords[0])

    bunch_canvas_x = canvas_center_x + bunch_xi * xi_scale
    bunch_canvas_y = canvas_center_y + bunch_y_center * y_scale

    if len(particles) < MAX_PARTICLES:
        spawn_n = min(50, MAX_PARTICLES - len(particles))
        for _ in range(spawn_n):
            is_witness = random.random() < 0.55
            if is_witness:
                # Spawn inside witness bunch core
                px = bunch_canvas_x + random.gauss(0.0, 18.0)
                py = bunch_canvas_y + random.gauss(0.0, 10.0)
                particles.append(RelativisticElectron(px, py, is_witness=True))
            else:
                # Spawn in ambient plasma sweeping into sheath
                theta = random.uniform(0.0, 2.0 * np.pi)
                r_spawn = random.uniform(1.6, 2.3) * y_scale
                px = canvas_center_x + XI_C * xi_scale + np.cos(theta) * r_spawn * 1.1
                py = canvas_center_y + np.sin(theta) * r_spawn
                particles.append(RelativisticElectron(px, py, is_witness=False))

    # 5. Advect and Render Relativistic Electrons
    py5.blend_mode(py5.ADD)
    active_particles = []

    for p in particles:
        gx = int(np.clip(((p.px / py5.width) * (Nx - 1)), 0, Nx - 1))
        gy = int(np.clip(((p.py / py5.height) * (Ny - 1)), 0, Ny - 1))

        flow_vx = float(u_axial[gy, gx]) * 3.8
        flow_vy = float(v_radial[gy, gx]) * 3.8
        ez_val = float(Ez_accel_core[gy, gx])
        fr_val = float(Fr_focus[gy, gx])

        p.update(ez_val, fr_val, flow_vx, flow_vy)

        if not p.is_dead:
            active_particles.append(p)

            life_norm = p.life / p.max_life
            alpha = int(255 * (life_norm if life_norm < 0.85 else (1.0 - life_norm) * 6.0))

            if p.is_witness:
                # Accelerated witness bunch: incandescent white-gold and synchrotron violet
                if p.energy > 25.0:
                    cr, cg, cb = 255, 250, 230
                else:
                    cr, cg, cb = 230, 140, 255
            else:
                # Sheath electron: radiant cyan / electric blue
                cr, cg, cb = 30, 210, 255

            # Particle outer halo
            py5.no_stroke()
            py5.fill(cr, cg, cb, int(alpha * 0.24))
            py5.circle(p.px, p.py, p.radius * 3.4)

            # High-intensity nucleus
            py5.fill(255, 255, 250, alpha)
            py5.circle(p.px, p.py, p.radius * 0.95)

            # Relativistic streak line
            py5.stroke(cr, cg, cb, int(alpha * 0.7))
            py5.stroke_weight(1.5)
            py5.line(p.px, p.py, p.prev_x, p.prev_y)

    particles = active_particles
    py5.blend_mode(py5.BLEND)

    # 6. Fail-safe blank screen check
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
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Electrons: {len(particles)}")

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

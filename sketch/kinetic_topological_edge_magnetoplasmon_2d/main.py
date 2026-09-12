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
x_coords = np.linspace(-3.8, 3.8, Nx, dtype=np.float32)
y_coords = np.linspace(-3.8 * (Ny / Nx), 3.8 * (Ny / Nx), Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)

R_grid = np.sqrt(X_grid**2 + Y_grid**2) + 1e-5
Theta_grid = np.arctan2(Y_grid, X_grid)

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Lagrangian Chiral Skipping Cyclotron Electrons
MAX_PARTICLES = 1200
particles = []


class SkippingElectron:
    def __init__(self, px, py, is_edge=True):
        self.px = px
        self.py = py
        self.prev_x = px
        self.prev_y = py
        self.is_edge = is_edge
        self.cyclotron_phase = random.uniform(0.0, 2.0 * np.pi)
        self.cyclotron_radius = random.uniform(4.5, 9.5) if is_edge else random.uniform(3.5, 7.5)
        self.life = random.uniform(90.0, 260.0) if is_edge else random.uniform(60.0, 180.0)
        self.max_life = self.life
        self.radius = random.uniform(1.5, 3.0) if is_edge else random.uniform(1.0, 2.0)
        self.tunneling = False

    def update(self, v_drift_x, v_drift_y, edge_proximity, is_qpc_junction, dt=1.0):
        self.prev_x = self.px
        self.prev_y = self.py

        # High-frequency cyclotron gyro-motion (omega_c = e*B/m)
        omega_c = 0.55
        self.cyclotron_phase += omega_c * dt

        # Cyclotron gyro-offset
        gyro_dx = self.cyclotron_radius * np.cos(self.cyclotron_phase)
        gyro_dy = self.cyclotron_radius * np.sin(self.cyclotron_phase)

        if self.is_edge:
            # Guiding center drifts strictly clockwise along the topological edge
            drift_speed = 3.6 + 1.4 * edge_proximity
            self.px += (v_drift_x * drift_speed + gyro_dx * 0.65) * dt
            self.py += (v_drift_y * drift_speed + gyro_dy * 0.65) * dt

            if is_qpc_junction and random.random() < 0.05:
                self.tunneling = True
        else:
            # Bulk electrons execute closed localized cyclotron loops with slow diamagnetic drift
            self.px += (v_drift_x * 0.35 + gyro_dx * 0.75) * dt
            self.py += (v_drift_y * 0.35 + gyro_dy * 0.75) * dt

        self.life -= 1.0

    @property
    def is_dead(self):
        return (
            self.life <= 0
            or self.px > py5.width + 80
            or self.px < -80
            or self.py > py5.height + 80
            or self.py < -80
        )


def compute_quantum_hall_fields(frame):
    """
    Computes topological chiral edge magnetoplasmon (EMP) electrodynamics:
    - Mesoscopic quantum Hall droplet boundary with quantum point contact (QPC)
    - Incompressible bulk Landau level insulator
    - Unidirectional clockwise chiral EMP density waves
    - QPC tunneling beam splitting and Aharonov-Bohm interference fringes
    - Chiral drift velocity vector field
    """
    t = frame / 60.0  # seconds

    # 1. Droplet Boundary Geometry: Bilateral Symmetrical QPC Constriction
    # Upper and lower boundaries pinch toward each other at X ~ 0 to form a narrow quantum point contact
    R0 = 2.15
    # Symmetric constriction at top and bottom: Y pinching at X ~ 0
    qpc_pinch = 0.62 * np.exp(- (X_grid**2) / 0.38) * (1.0 + 0.35 * np.cos(2.0 * Theta_grid)**2)
    droplet_radius_field = R0 * (
        1.0
        + 0.16 * np.cos(2.0 * Theta_grid)
        + 0.07 * np.sin(4.0 * Theta_grid)
    ) - qpc_pinch * np.abs(np.sin(Theta_grid))

    # Radial distance normalized to droplet boundary
    r_norm = R_grid / (droplet_radius_field + 1e-4)

    # Incompressible bulk Landau state (interior: r_norm < 1)
    bulk_state = np.clip(1.0 - (r_norm)**7.0, 0.0, 1.0)

    # Topological chiral edge channel: thin boundary ring where gap closes
    edge_width = 0.082
    edge_dist = np.abs(r_norm - 1.0)
    topological_edge = np.exp(- (edge_dist**2) / (2.0 * (edge_width**2)))

    # 2. Chiral Edge Magnetoplasmons (EMPs) with High Wave Contrast
    # Unidirectional clockwise acoustic charge-density wave
    emp_speed = 1.35  # rad/s clockwise
    phase_emp = Theta_grid - emp_speed * t

    emp_wave_m1 = 1.0 * np.cos(phase_emp)
    emp_wave_m2 = 0.75 * np.cos(2.0 * phase_emp + 0.4)
    emp_wave_m3 = 0.50 * np.cos(3.0 * phase_emp - 0.7)
    emp_wave_m4 = 0.35 * np.cos(4.0 * phase_emp + 1.1)

    emp_total_wave = (emp_wave_m1 + emp_wave_m2 + emp_wave_m3 + emp_wave_m4) / 2.6
    # Deep, vivid contrast modulation along the topological edge
    emp_charge_density = topological_edge * (1.0 + 0.95 * emp_total_wave)

    # 3. Bilateral Quantum Point Contact (QPC) Constriction & Tunneling Junction
    # Smooth, continuous Gaussian/quartic envelope without hard rectangular boundaries
    qpc_envelope = np.exp(- ((X_grid / 0.52)**4) - ((Y_grid / 0.78)**4))
    qpc_junction = np.exp(- (X_grid**2) / 0.16 - (Y_grid**2) / 0.25) * qpc_envelope

    # Aharonov-Bohm quantum phase interference fringes across the tunneling junction
    ab_freq = 16.0
    ab_fringes = np.cos(ab_freq * X_grid + 5.0 * t) * np.exp(- (Y_grid**2) / 0.16) * qpc_junction

    # 4. Chiral Drift Velocity Field for Skipping Electrons
    tangent_x = np.sin(Theta_grid)
    tangent_y = -np.cos(Theta_grid)

    v_drift_x = np.where(
        topological_edge > 0.08,
        tangent_x * (1.0 + 0.45 * emp_total_wave),
        tangent_x * 0.15
    )
    v_drift_y = np.where(
        topological_edge > 0.08,
        tangent_y * (1.0 + 0.45 * emp_total_wave),
        tangent_y * 0.15
    )

    # QPC tunneling cross-flow
    tunnel_flow = qpc_junction * np.sign(Y_grid) * 0.75
    v_drift_y += -tunnel_flow

    return (
        bulk_state,
        topological_edge,
        emp_charge_density,
        qpc_junction,
        ab_fringes,
        v_drift_x,
        v_drift_y,
        droplet_radius_field,
    )


def render_quantum_hall_canvas(
    bulk_state,
    topological_edge,
    emp_charge_density,
    qpc_junction,
    ab_fringes,
    frame,
):
    """
    Renders 4-channel image into pixel_buffer using strict 60-30-10 palette rules:
    - 60% Cryogenic Dilution Obsidian Void & Bulk Incompressible Landau Indigo (#01030a, #081226, #121e3c)
    - 30% Chiral Topological Edge Electric Cyan & Emerald Mint (#00f0ff, #10b981, #06b6d4)
    - 10% QPC Tunneling Solar Gold & Aharonov-Bohm Phase Violet (#ffffff, #fbbf24, #e879f9, #c084fc)
    """
    # Background: Cryogenic vacuum obsidian void with subtle radial cooling gradient
    bg_r = 1.0 + 1.2 * np.cos(R_grid * 0.4)
    bg_g = 3.0 + 1.5 * np.cos(R_grid * 0.35)
    bg_b = 9.0 + 4.0 * np.sin(R_grid * 0.3)

    # Dominant 60%: Incompressible bulk Landau level interior
    bulk_indigo = bulk_state * 0.85
    r_dom = bg_r + bulk_indigo * 10.0
    g_dom = bg_g + bulk_indigo * 24.0
    b_dom = bg_b + bulk_indigo * 68.0

    # Secondary 30%: Chiral Topological Edge Magnetoplasmon Ribbon
    # Electric Cyan (#00f0ff) & Emerald Mint (#10b981)
    cyan_intensity = emp_charge_density * 1.5 + topological_edge * 0.6
    mint_intensity = np.maximum(0.0, emp_charge_density - 0.8) * 0.8

    cyan_r = cyan_intensity * 6.0 + mint_intensity * 16.0
    cyan_g = cyan_intensity * 195.0 + mint_intensity * 185.0
    cyan_b = cyan_intensity * 255.0 + mint_intensity * 129.0

    # Accent 10%: QPC Tunneling Constriction Solar Gold & AB Phase Violet
    # Incandescent gold center (#ffffff, #fbbf24) with violet interference halos (#e879f9)
    qpc_intensity = qpc_junction * 1.8
    ab_intensity = np.maximum(0.0, ab_fringes) * 1.4

    accent_r = qpc_intensity * 255.0 + ab_intensity * 230.0
    accent_g = qpc_intensity * 220.0 + ab_intensity * 120.0
    accent_b = qpc_intensity * 120.0 + ab_intensity * 255.0

    # Composite layers
    R_total = np.clip(r_dom + cyan_r + accent_r, 0.0, 255.0)
    G_total = np.clip(g_dom + cyan_g + accent_g, 0.0, 255.0)
    B_total = np.clip(b_dom + cyan_b + accent_b, 0.0, 255.0)

    # Soft cinematic vignette around canvas borders
    vig_x = np.clip(1.0 - (X_grid / 3.8)**4, 0.0, 1.0)
    vig_y = np.clip(1.0 - (Y_grid / (3.8 * (Ny / Nx)))**4, 0.0, 1.0)
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
    py5.background(1, 3, 9)


def draw_frame():
    global particles

    # 1. Physics field computation
    (
        bulk_state,
        topological_edge,
        emp_charge_density,
        qpc_junction,
        ab_fringes,
        v_drift_x,
        v_drift_y,
        droplet_radius_field,
    ) = compute_quantum_hall_fields(py5.frame_count)

    # 2. Render field into pixel buffer
    render_quantum_hall_canvas(
        bulk_state,
        topological_edge,
        emp_charge_density,
        qpc_junction,
        ab_fringes,
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

    # 4. Lagrangian Skipping Electron Spawning
    canvas_center_x = py5.width / 2.0
    canvas_center_y = py5.height / 2.0
    scale_factor = py5.height / (y_coords[-1] - y_coords[0])

    if len(particles) < MAX_PARTICLES:
        spawn_n = min(45, MAX_PARTICLES - len(particles))
        for _ in range(spawn_n):
            is_edge = random.random() < 0.72
            theta = random.uniform(0.0, 2.0 * np.pi)

            if is_edge:
                # Spawn along constricted topological boundary
                qpc_p = 0.62 * np.exp(- ((2.15 * np.cos(theta))**2) / 0.38) * np.abs(np.sin(theta))
                r_base = 2.15 * (1.0 + 0.16 * np.cos(2.0 * theta) + 0.07 * np.sin(4.0 * theta)) - qpc_p
                r_spawn = (r_base + random.uniform(-0.06, 0.06)) * scale_factor
                px = canvas_center_x + np.cos(theta) * r_spawn
                py = canvas_center_y + np.sin(theta) * r_spawn
                particles.append(SkippingElectron(px, py, is_edge=True))
            else:
                # Spawn in bulk interior
                r_spawn = random.uniform(0.2, 1.7) * scale_factor
                px = canvas_center_x + np.cos(theta) * r_spawn
                py = canvas_center_y + np.sin(theta) * r_spawn
                particles.append(SkippingElectron(px, py, is_edge=False))

    # 5. Advect and Render Skipping Cyclotron Electrons
    py5.blend_mode(py5.ADD)
    active_particles = []

    for p in particles:
        gx = int(np.clip(((p.px / py5.width) * (Nx - 1)), 0, Nx - 1))
        gy = int(np.clip(((p.py / py5.height) * (Ny - 1)), 0, Ny - 1))

        drift_x = float(v_drift_x[gy, gx])
        drift_y = float(v_drift_y[gy, gx])
        edge_prox = float(topological_edge[gy, gx])
        is_qpc = float(qpc_junction[gy, gx]) > 0.25

        p.update(drift_x, drift_y, edge_prox, is_qpc)

        if not p.is_dead:
            active_particles.append(p)

            life_norm = p.life / p.max_life
            alpha = int(255 * (life_norm if life_norm < 0.85 else (1.0 - life_norm) * 6.0))

            if p.tunneling or is_qpc:
                # QPC Tunneling electron: incandescent solar gold (#fbbf24) and white
                cr, cg, cb = 255, 235, 140
            elif p.is_edge:
                # Chiral edge skipping electron: electric cyan (#00f0ff) and mint
                cr, cg, cb = 16, 235, 255
            else:
                # Bulk localized electron: deep indigo glow
                cr, cg, cb = 70, 110, 255

            # Particle outer halo
            py5.no_stroke()
            py5.fill(cr, cg, cb, int(alpha * 0.26))
            py5.circle(p.px, p.py, p.radius * 3.4)

            # High-intensity nucleus
            py5.fill(255, 255, 250, alpha)
            py5.circle(p.px, p.py, p.radius * 0.95)

            # Cycloidal skipping streak line
            py5.stroke(cr, cg, cb, int(alpha * 0.75))
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
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Skipping Electrons: {len(particles)}")

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

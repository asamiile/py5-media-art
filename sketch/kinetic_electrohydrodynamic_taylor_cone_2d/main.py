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
x_coords = np.linspace(-4.8, 4.8, Nx, dtype=np.float32)
y_coords = np.linspace(-2.7, 2.7, Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Lagrangian Electrospray Ion Droplets
MAX_IONS = 1100
ion_particles = []


class IonDroplet:
    def __init__(self, px, py, vx, vy, charge):
        self.px = px
        self.py = py
        self.prev_x = px
        self.prev_y = py
        self.vx = vx
        self.vy = vy
        self.charge = charge
        self.life = random.uniform(65.0, 185.0)
        self.max_life = self.life
        self.radius = random.uniform(1.6, 3.4)

    def update(self, ex, ey, whipping_drift):
        self.prev_x = self.px
        self.prev_y = self.py

        # Electrostatic acceleration + Coulomb expansion + whipping inertia
        ax = self.charge * ex * 1.8 + whipping_drift
        ay = self.charge * ey * 1.8

        self.vx = self.vx * 0.93 + ax * 0.14 + random.uniform(-0.1, 0.1)
        self.vy = self.vy * 0.93 + ay * 0.14 + random.uniform(-0.05, 0.05)

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


def compute_ehd_field(frame_idx):
    # Normalized time tau in [0, 2*pi]
    tau = (2.0 * np.pi * frame_idx) / TOTAL_FRAMES

    # Cyclic electric potential modulation (breathing voltage)
    v_mod = 0.88 + 0.22 * np.sin(tau)

    # Base meniscus base at y = -2.1
    y_base = -2.1

    # Taylor Cone Apex coordinates
    apex_x = 0.15 * np.sin(2.0 * tau)
    apex_y = -0.35 + 0.38 * np.sin(tau)  # Rises as voltage peaks

    # Distance from cone apex
    dx_apex = X_grid - apex_x
    dy_apex = Y_grid - apex_y

    # Angle relative to vertical axis (0 is straight up towards counter-electrode)
    theta_apex = np.arctan2(np.abs(dx_apex), dy_apex)
    r_apex = np.sqrt(dx_apex**2 + dy_apex**2) + 1e-5

    # Taylor cone half-angle theta_c = 49.3 degrees = 0.8604 radians
    # In cone coordinate system, liquid occupies angle > (pi - theta_c)
    theta_c = 0.8604
    cone_boundary_angle = np.pi - theta_c

    # Analytical Taylor cone liquid profile:
    # Blend from hyperbolic meniscus base to sharp 49.3-deg cone near apex
    cone_profile_y = apex_y - np.abs(dx_apex) / np.tan(theta_c)
    smooth_meniscus_y = y_base + (apex_y - y_base) * np.exp(- (dx_apex / 1.4)**2)

    # Liquid height profile H_liquid(x):
    h_liquid_y = np.maximum(cone_profile_y, smooth_meniscus_y)

    # Liquid domain mask (1 inside liquid, 0 in vacuum)
    liquid_dist = Y_grid - h_liquid_y
    liquid_mask = 0.5 * (1.0 - np.tanh(liquid_dist / 0.04))

    # Meniscus boundary surface crest
    meniscus_crest = np.exp(- (liquid_dist / 0.06)**2)

    # Taylor cone singular tip intensity
    tip_intensity = np.exp(- (r_apex / 0.22)**2) * v_mod

    # Electrostatic Potential Field Phi(x, y):
    # Solves Laplace with conducting cone + upper ground electrode at y = 2.4
    # Near cone tip, |E| ~ r^(-1/2)
    phi_background = (Y_grid - y_base) / (2.4 - y_base)
    phi_cone = (1.0 - np.exp(- (r_apex / 2.8)**0.55)) * np.cos(0.5 * theta_apex)
    phi = (0.35 * phi_background + 0.65 * phi_cone) * v_mod
    phi = np.where(liquid_mask > 0.5, 0.0, phi)

    # Equipotential lines (Ionizing violet filaments in vacuum)
    k_pot = 28.0
    pot_phase = k_pot * phi
    pot_filaments = np.exp(- ((np.sin(pot_phase)) / 0.22)**2) * (1.0 - liquid_mask)

    # Electric Field Vector E = -grad(Phi)
    ey = -np.gradient(phi, axis=0) * (Ny / 5.4)
    ex = -np.gradient(phi, axis=1) * (Nx / 9.6)
    e_mag = np.sqrt(ex**2 + ey**2) + 1e-5

    # Whipping jet trajectory above cone apex (y > apex_y):
    # Bending / whipping instability equation:
    whip_amp = 0.42 * (0.5 + 0.5 * np.sin(tau))
    whip_wave = whip_amp * (np.maximum(0.0, dy_apex) / 1.8)**1.6 * np.sin(4.5 * dy_apex - 3.0 * tau)
    dist_to_jet = np.abs(dx_apex - whip_wave)

    # Jet core intensity
    jet_core = np.exp(- (dist_to_jet / 0.045)**2) * (dy_apex > 0.0) * np.exp(- (dy_apex / 2.6))

    # 3D Specular lighting on meniscus surface
    dh_dy = np.gradient(liquid_mask, axis=0) * (Ny / 5.4)
    dh_dx = np.gradient(liquid_mask, axis=1) * (Nx / 9.6)
    norm_len = np.sqrt(dh_dx**2 + dh_dy**2 + 1.0)
    nx = -dh_dx / norm_len
    ny = -dh_dy / norm_len
    nz = 1.0 / norm_len

    # Specular reflections:
    # Light 1 (Neon Violet Key Light from top-left: [-0.5, 0.6, 0.62])
    lx1, ly1, lz1 = -0.5, 0.6, 0.62
    h1x, h1y, h1z = lx1, ly1, lz1 + 1.0
    h1_len = np.sqrt(h1x**2 + h1y**2 + h1z**2)
    spec1 = np.maximum(0.0, nx * (h1x / h1_len) + ny * (h1y / h1_len) + nz * (h1z / h1_len))**24

    # Light 2 (Ozone Cyan Rim Light from top-right: [0.5, 0.6, 0.62])
    lx2, ly2, lz2 = 0.5, 0.6, 0.62
    h2x, h2y, h2z = lx2, ly2, lz2 + 1.0
    h2_len = np.sqrt(h2x**2 + h2y**2 + h2z**2)
    spec2 = np.maximum(0.0, nx * (h2x / h2_len) + ny * (h2y / h2_len) + nz * (h2z / h2_len))**32

    # Vignette
    r_center = np.sqrt((X_grid / 4.4)**2 + (Y_grid / 2.5)**2)
    vignette = np.exp(- r_center**6)

    return (
        liquid_mask, meniscus_crest, tip_intensity,
        pot_filaments, jet_core,
        spec1, spec2, vignette,
        ex, ey, apex_x, apex_y, whip_amp
    )


def render_ehd_canvas(liquid_mask, meniscus_crest, tip_intensity, pot_filaments, jet_core, spec1, spec2, vignette):
    # Palette Construction:
    # 1. 60% Matrix: High-Voltage Vacuum Obsidian (#030208) & Deep Royal Amethyst (#1e0836)
    r = np.full_like(X_grid, 3.0)
    g = np.full_like(X_grid, 2.0)
    b = np.full_like(X_grid, 8.0)

    # Ambient liquid bulk (Deep Amethyst / Sapphire)
    r += liquid_mask * 42.0 * vignette
    g += liquid_mask * 12.0 * vignette
    b += liquid_mask * 90.0 * vignette

    # 2. 30% Ionizing Neon Violet & Ozone Cyan (#8b5cf6, #06b6d4)
    # Equipotential contour lines
    cyan_filaments = pot_filaments * vignette
    r += cyan_filaments * 12.0
    g += cyan_filaments * 185.0
    b += cyan_filaments * 225.0

    # Meniscus surface crest glow (Neon Violet)
    crest_glow = meniscus_crest * vignette
    r += crest_glow * 170.0
    g += crest_glow * 50.0
    b += crest_glow * 250.0

    # Specular highlights (Liquid sheen)
    r += spec1 * liquid_mask * vignette * 180.0
    g += spec1 * liquid_mask * vignette * 70.0
    b += spec1 * liquid_mask * vignette * 255.0

    r += spec2 * liquid_mask * vignette * 40.0
    g += spec2 * liquid_mask * vignette * 230.0
    b += spec2 * liquid_mask * vignette * 255.0

    # 3. 10% Incandescent Solar White-Gold (#fffbeb, #fef08a)
    # Taylor cone singular tip
    tip_glow = tip_intensity * vignette
    r += tip_glow * 255.0
    g += tip_glow * 250.0
    b += tip_glow * 210.0

    # Whipping micro-jet core
    jet_glow = jet_core * vignette
    r += jet_glow * 255.0
    g += jet_glow * 235.0
    b += jet_glow * 150.0

    # Populate ARGB pixel buffer
    pixel_buffer[..., 0] = 255
    pixel_buffer[..., 1] = np.clip(r, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b, 0, 255).astype(np.uint8)


def draw_frame():
    global ion_particles

    # 1. Physics field computation
    (liquid_mask, meniscus_crest, tip_intensity,
     pot_filaments, jet_core,
     spec1, spec2, vignette,
     ex, ey, apex_x, apex_y, whip_amp) = compute_ehd_field(py5.frame_count)

    # 2. Render pixel buffer
    render_ehd_canvas(liquid_mask, meniscus_crest, tip_intensity, pot_filaments, jet_core, spec1, spec2, vignette)

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

    # 4. Ion particle emission at Taylor Cone apex and whipping jet
    # Convert apex coordinates to canvas pixels
    apex_px = ((apex_x - x_coords[0]) / (x_coords[-1] - x_coords[0])) * py5.width
    apex_py = ((apex_y - y_coords[0]) / (y_coords[-1] - y_coords[0])) * py5.height

    if len(ion_particles) < MAX_IONS:
        spawn_n = min(40, MAX_IONS - len(ion_particles))
        for _ in range(spawn_n):
            angle = random.uniform(0.35 * np.pi, 0.65 * np.pi)  # Upward cone
            speed = random.uniform(8.0, 16.0)
            vx = np.cos(angle) * speed
            vy = -np.sin(angle) * speed  # Screen y points downward
            charge = random.uniform(0.8, 1.4)
            ion_particles.append(IonDroplet(apex_px + random.uniform(-4, 4), apex_py - random.uniform(0, 10), vx, vy, charge))

    # 5. Advect and render ion droplet sparks in ADD blend mode
    py5.blend_mode(py5.ADD)
    active_ions = []

    for p in ion_particles:
        gx = int(np.clip((p.px / py5.width) * (Nx - 1), 0, Nx - 1))
        gy = int(np.clip((p.py / py5.height) * (Ny - 1), 0, Ny - 1))

        local_ex = ex[gy, gx]
        local_ey = ey[gy, gx]
        local_pot = pot_filaments[gy, gx]

        # Whipping lateral force
        whipping_drift = whip_amp * np.sin(p.py * 0.02 - py5.frame_count * 0.1) * 0.35

        p.update(local_ex, -local_ey, whipping_drift)

        if not p.is_dead:
            active_ions.append(p)
            life_norm = p.life / p.max_life
            alpha = int(life_norm * (165 + local_pot * 90))

            # Color shift: Incandescent White at apex -> Neon Cyan & Violet in plume
            if life_norm > 0.75:
                cr = 255
                cg = int(245 + life_norm * 10)
                cb = int(190 + life_norm * 65)
            elif life_norm > 0.35:
                cr = int(40 + life_norm * 80)
                cg = int(220 + life_norm * 30)
                cb = 255
            else:
                cr = int(180 + life_norm * 60)
                cg = int(80 + life_norm * 80)
                cb = 255

            # Particle aura glow
            py5.no_stroke()
            py5.fill(cr, cg, cb, int(alpha * 0.34))
            py5.circle(p.px, p.py, p.radius * 2.8)

            # Particle nucleus
            py5.fill(255, 255, 250, alpha)
            py5.circle(p.px, p.py, p.radius * 0.9)

            # Ion streak filament
            py5.stroke(cr, cg, cb, int(alpha * 0.52))
            py5.stroke_weight(1.2)
            py5.line(p.px, p.py, p.prev_x, p.prev_y)

    ion_particles = active_ions
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
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Active Ions: {len(ion_particles)}")

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

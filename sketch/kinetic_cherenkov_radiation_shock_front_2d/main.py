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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Spatial Simulation Grid (16:9 aspect ratio, higher resolution grid for ultra-smooth wavefronts)
Nx, Ny = 800, 450
x_coords = np.linspace(-4.0, 4.0, Nx, dtype=np.float32)
y_coords = np.linspace(-2.25, 2.25, Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
dx = float(x_coords[1] - x_coords[0])
dy = float(y_coords[1] - y_coords[0])

# Physical Parameters for Dielectric Medium (Cherenkov in Heavy Water)
# Refractive index n = 1.35; Phase velocity c_medium = 1.0 / n
n_refract = 1.35
c_medium = 1.0 / n_refract
beta_particle = 0.96  # Relativistic particle velocity v / c_0
cos_theta_c = 1.0 / (beta_particle * n_refract)
theta_cherenkov = float(np.arccos(np.clip(cos_theta_c, -1.0, 1.0)))
sin_theta_c = float(np.sin(theta_cherenkov))

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Dual Light Vectors for Specular Caustic Shading
light1 = np.array([0.55, -0.60, 0.58], dtype=np.float32)
light1 /= np.linalg.norm(light1)
light2 = np.array([-0.50, 0.55, 0.67], dtype=np.float32)
light2 /= np.linalg.norm(light2)
view_vec = np.array([0.0, 0.0, 1.0], dtype=np.float32)
h1 = (light1 + view_vec) / np.linalg.norm(light1 + view_vec)
h2 = (light2 + view_vec) / np.linalg.norm(light2 + view_vec)

# Lagrangian Particles: Scintillation Photons, Ionization Trail Embers & Delta-Ray Branch Sparks
MAX_PARTICLES = 1600
particles = []


class QuantumParticle:
    def __init__(self, px, py, ptype="photon", vx=0.0, vy=0.0, life=120.0, radius=1.8):
        self.px = px
        self.py = py
        self.prev_x = px
        self.prev_y = py
        self.ptype = ptype  # "photon", "ion", "delta"
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.radius = radius

    def update(self, dt=1.0):
        self.prev_x = self.px
        self.prev_y = self.py

        if self.ptype == "photon":
            self.px += self.vx * dt
            self.py += self.vy * dt
            self.vx *= 0.995
            self.vy *= 0.995
        elif self.ptype == "ion":
            self.px += (self.vx + random.uniform(-0.3, 0.3)) * dt
            self.py += (self.vy + random.uniform(-0.3, 0.3)) * dt
            self.vx *= 0.96
            self.vy *= 0.96
        elif self.ptype == "delta":
            self.px += self.vx * dt
            self.py += self.vy * dt
            self.vx *= 0.97
            self.vy *= 0.97

        self.life -= 1.0

    @property
    def is_dead(self):
        return (
            self.life <= 0
            or self.px > py5.width + 120
            or self.px < -120
            or self.py > py5.height + 120
            or self.py < -120
        )


def get_primary_trajectory(t_norm):
    """
    Returns the relativistic particle's position, velocity, and orientation:
    Smooth sweeping Lorentz cyclotron curve across the detector.
    """
    px = -3.8 + 7.6 * t_norm
    py = 0.65 * np.sin(2.0 * np.pi * t_norm * 1.5 - 0.3) + 0.25 * np.sin(4.0 * np.pi * t_norm)

    dt = 0.001
    px_next = -3.8 + 7.6 * (t_norm + dt)
    py_next = 0.65 * np.sin(2.0 * np.pi * (t_norm + dt) * 1.5 - 0.3) + 0.25 * np.sin(4.0 * np.pi * (t_norm + dt))

    vx = (px_next - px) / dt
    vy = (py_next - py) / dt
    speed = np.sqrt(vx**2 + vy**2)
    heading = np.arctan2(vy, vx)

    return px, py, vx / speed, vy / speed, heading


def compute_cherenkov_fields(frame):
    """
    Synthesizes the electrodynamic Cherenkov shock front fields without sharp step-function cutoffs:
    - Smooth continuous Huygens envelope with Frank-Tamm chromatic dispersion
    - Anti-aliased optical wave interference fringes
    - Smooth secondary Bremsstrahlung daughter cones
    - Soft Blinn-Phong specular caustic normal shading
    """
    t_norm = frame / TOTAL_FRAMES
    px, py, dir_x, dir_y, heading = get_primary_trajectory(t_norm)

    # Relative coordinates from particle position
    dx_rel = X_grid - px
    dy_rel = Y_grid - py

    # Longitudinal coordinate along particle velocity (positive ahead, negative behind)
    L_coord = dx_rel * dir_x + dy_rel * dir_y
    # Transverse distance perpendicular to particle velocity
    T_coord = -dx_rel * dir_y + dy_rel * dir_x
    T_abs = np.abs(T_coord)

    # Smooth continuous distance to the Cherenkov shock cone envelope
    dist_cone = -L_coord * sin_theta_c - T_abs * cos_theta_c

    # Smooth sigmoidal precursor envelope ahead of particle (replaces sharp conditionals)
    cone_existence = 1.0 / (1.0 + np.exp(L_coord * 6.0))

    # Primary blue shock wavefront with smooth exponential transition
    # Sigmoidal transition across the shock front
    sigmoid_front = 1.0 / (1.0 + np.exp(-dist_cone * 35.0))
    shock_front_blue = (
        sigmoid_front * np.exp(-np.maximum(0.0, dist_cone) * 1.8)
        * (np.cos(np.maximum(0.0, dist_cone) * 22.0)**2 * 0.65 + 0.35)
        + (1.0 - sigmoid_front) * np.exp(np.minimum(0.0, dist_cone) * 18.0)
    ) * cone_existence

    # Frank-Tamm Dispersion: Actinic Ultraviolet wavefront with slightly steeper angle
    sin_theta_uv = sin_theta_c * 1.032
    cos_theta_uv = np.sqrt(max(0.0, 1.0 - sin_theta_uv**2))
    dist_cone_uv = -L_coord * sin_theta_uv - T_abs * cos_theta_uv
    sigmoid_front_uv = 1.0 / (1.0 + np.exp(-dist_cone_uv * 38.0))
    shock_front_uv = (
        sigmoid_front_uv * np.exp(-np.maximum(0.0, dist_cone_uv) * 2.2)
        * (np.cos(np.maximum(0.0, dist_cone_uv) * 26.0)**2 * 0.70 + 0.30)
        + (1.0 - sigmoid_front_uv) * np.exp(np.minimum(0.0, dist_cone_uv) * 20.0)
    ) * cone_existence

    # Primary particle core intense ionization peak
    dist_core_sq = dx_rel**2 + dy_rel**2
    core_glow = np.exp(- dist_core_sq / 0.04) * 3.2

    # Smooth Bremsstrahlung Daughter Cones (secondary deceleration events)
    daughter_cones = np.zeros_like(X_grid)
    for k in range(1, 4):
        t_past = max(0.0, t_norm - k * 0.08)
        px_k, py_k, dx_k, dy_k, _ = get_primary_trajectory(t_past)
        dx_k_rel = X_grid - px_k
        dy_k_rel = Y_grid - py_k
        L_k = dx_k_rel * dx_k + dy_k_rel * dy_k
        T_k = np.abs(-dx_k_rel * dy_k + dy_k_rel * dx_k)
        dist_k = -L_k * sin_theta_c - T_k * cos_theta_c
        age = (t_norm - t_past) * 12.0
        decay = np.exp(-age * 1.8)

        sig_k = 1.0 / (1.0 + np.exp(-dist_k * 30.0))
        exist_k = 1.0 / (1.0 + np.exp(L_k * 5.0))
        sub_cone = (
            sig_k * np.exp(-np.maximum(0.0, dist_k) * 2.5) * np.cos(np.maximum(0.0, dist_k) * 18.0)**2
            + (1.0 - sig_k) * np.exp(np.minimum(0.0, dist_k) * 15.0)
        ) * exist_k * decay
        daughter_cones += sub_cone

    # Smooth continuous ionization wake (Gaussian transverse profile, no hard cutoff)
    wake_longitudinal = 1.0 / (1.0 + np.exp(L_coord * 4.0)) * np.exp(L_coord * 0.25)
    wake_transverse = np.exp(- (T_abs / 0.55)**2)
    wake_ripples = (
        wake_longitudinal * wake_transverse
        * (np.cos(L_coord * 12.0 - frame * 0.20)**2 * 0.6 + 0.4)
    )

    # Combined Optical Energy Density
    I_total = (
        shock_front_blue * 1.35
        + shock_front_uv * 1.15
        + daughter_cones * 0.55
        + wake_ripples * 0.50
        + core_glow
    )

    # 3D Blinn-Phong Specular Caustic Normal Shading
    # Smooth energy landscape to avoid high-frequency gradient aliasing
    H_surf = np.sqrt(np.clip(I_total, 0.0, 4.0)) * 0.60
    grad_H_y, grad_H_x = np.gradient(H_surf, dy, dx)
    norm_denom = np.sqrt(grad_H_x**2 + grad_H_y**2 + 1.0)
    Nx_s = -grad_H_x / norm_denom
    Ny_s = -grad_H_y / norm_denom
    Nz_s = 1.0 / norm_denom

    spec1 = np.maximum(0.0, Nx_s * h1[0] + Ny_s * h1[1] + Nz_s * h1[2])**18
    spec2 = np.maximum(0.0, Nx_s * h2[0] + Ny_s * h2[1] + Nz_s * h2[2])**14

    return (
        I_total,
        shock_front_blue,
        shock_front_uv,
        core_glow,
        spec1,
        spec2,
        px,
        py,
        dir_x,
        dir_y,
        heading,
    )


def render_cherenkov_canvas(
    I_total,
    shock_front_blue,
    shock_front_uv,
    core_glow,
    spec1,
    spec2,
):
    """
    Renders 4-channel image into pixel_buffer following 60-30-10 palette rules:
    - 60% Reactor Pool Obsidian Void & Midnight Indigo Abyss (#02040a, #070e24, #0d1738)
    - 30% Cherenkov Electric Cyan & Actinic Ultraviolet (#06b6d4, #38bdf8, #4f46e5, #7c3aed)
    - 10% Incandescent Lepton Core Diamond-White & Bremsstrahlung Gold (#ffffff, #fef08a)
    """
    # 1. Background 60%: Reactor Pool Obsidian Void with deep optical water depth gradient
    r_bg = 2.0 + np.exp(- (X_grid**2 + Y_grid**2) / 6.0) * 4.0
    g_bg = 4.0 + np.exp(- (X_grid**2 + Y_grid**2) / 6.0) * 8.0
    b_bg = 10.0 + np.exp(- (X_grid**2 + Y_grid**2) / 6.0) * 26.0

    # 2. Dominant & Secondary 30%: Cherenkov Electric Cyan (#06b6d4) & Actinic Ultraviolet (#7c3aed)
    cyan_intensity = np.clip(shock_front_blue * 1.15, 0.0, 2.0)
    r_cyan = cyan_intensity * 6.0
    g_cyan = cyan_intensity * 182.0
    b_cyan = cyan_intensity * 212.0

    uv_intensity = np.clip(shock_front_uv * 1.25, 0.0, 2.0)
    r_uv = uv_intensity * 124.0
    g_uv = uv_intensity * 58.0
    b_uv = uv_intensity * 237.0

    # Specular reflections: liquid chromium caustic fringes
    spec_r = spec1 * 160.0 + spec2 * 210.0
    spec_g = spec1 * 220.0 + spec2 * 230.0
    spec_b = spec1 * 255.0 + spec2 * 255.0

    # Combined secondary emission
    r_shock = r_cyan * 0.65 + r_uv * 0.35 + spec_r * 0.35
    g_shock = g_cyan * 0.70 + g_uv * 0.30 + spec_g * 0.35
    b_shock = b_cyan * 0.60 + b_uv * 0.40 + spec_b * 0.35

    blend_factor = np.clip(I_total * 0.85, 0.0, 1.0)
    r_mid = r_bg * (1.0 - blend_factor) + r_shock * blend_factor
    g_mid = g_bg * (1.0 - blend_factor) + g_shock * blend_factor
    b_mid = b_bg * (1.0 - blend_factor) + b_shock * blend_factor

    # 3. Accent 10%: Incandescent Lepton Core Diamond-White & Solar Gold Caustics
    accent_core = np.clip(core_glow * 0.95 + spec1 * 0.35, 0.0, 3.0)
    r_accent = accent_core * 255.0
    g_accent = accent_core * 250.0
    b_accent = accent_core * 240.0

    # Final pixel buffer compilation clamped to uint8
    r_final = np.clip(r_mid + r_accent, 0.0, 255.0).astype(np.uint8)
    g_final = np.clip(g_mid + g_accent, 0.0, 255.0).astype(np.uint8)
    b_final = np.clip(b_mid + b_accent, 0.0, 255.0).astype(np.uint8)

    pixel_buffer[..., 1] = r_final
    pixel_buffer[..., 2] = g_final
    pixel_buffer[..., 3] = b_final


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw_frame():
    global particles

    # 1. Compute Cherenkov shock wave fields
    (
        I_total,
        shock_front_blue,
        shock_front_uv,
        core_glow,
        spec1,
        spec2,
        px,
        py,
        dir_x,
        dir_y,
        heading,
    ) = compute_cherenkov_fields(py5.frame_count)

    # 2. Render pixel buffer canvas
    render_cherenkov_canvas(
        I_total,
        shock_front_blue,
        shock_front_uv,
        core_glow,
        spec1,
        spec2,
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

    # 4. Convert primary particle coordinates from simulation grid to screen coordinates
    screen_px = (px - x_coords[0]) / (x_coords[-1] - x_coords[0]) * py5.width
    screen_py = (py - y_coords[0]) / (y_coords[-1] - y_coords[0]) * py5.height

    # 5. Spawn Lagrangian Quantum Particles
    if len(particles) < MAX_PARTICLES:
        spawn_n = min(40, MAX_PARTICLES - len(particles))
        for _ in range(spawn_n):
            roll = random.random()

            if roll < 0.60:
                # Scintillation Photons: Launched along Cherenkov cone wavefront
                side = 1.0 if random.random() < 0.5 else -1.0
                launch_angle = heading + side * (np.pi - theta_cherenkov) + random.gauss(0.0, 0.08)
                speed = random.uniform(3.5, 7.2)
                vx = np.cos(launch_angle) * speed
                vy = np.sin(launch_angle) * speed
                dist_back = random.uniform(0.0, 420.0)
                offset_x = -dir_x * dist_back + (-dir_y * side) * dist_back * np.tan(theta_cherenkov)
                offset_y = -dir_y * dist_back + (dir_x * side) * dist_back * np.tan(theta_cherenkov)
                particles.append(QuantumParticle(
                    screen_px + offset_x,
                    screen_py + offset_y,
                    ptype="photon",
                    vx=vx,
                    vy=vy,
                    life=random.uniform(50.0, 110.0),
                    radius=random.uniform(1.2, 2.6)
                ))

            elif roll < 0.85:
                # Ionization Wake Embers: Trailing along the primary track
                trail_dist = random.uniform(10.0, 600.0)
                px_ember = screen_px - dir_x * trail_dist + random.gauss(0.0, 16.0)
                py_ember = screen_py - dir_y * trail_dist + random.gauss(0.0, 16.0)
                particles.append(QuantumParticle(
                    px_ember,
                    py_ember,
                    ptype="ion",
                    vx=random.uniform(-0.6, 0.6),
                    vy=random.uniform(-0.6, 0.6),
                    life=random.uniform(90.0, 190.0),
                    radius=random.uniform(1.4, 3.2)
                ))

            else:
                # Delta-Ray Cascade Branch Sparks: High-speed secondary electrons
                branch_angle = heading + random.choice([-1.0, 1.0]) * random.uniform(0.8, 1.5)
                speed = random.uniform(6.0, 12.0)
                particles.append(QuantumParticle(
                    screen_px + random.gauss(0.0, 8.0),
                    screen_py + random.gauss(0.0, 8.0),
                    ptype="delta",
                    vx=np.cos(branch_angle) * speed,
                    vy=np.sin(branch_angle) * speed,
                    life=random.uniform(25.0, 55.0),
                    radius=random.uniform(2.0, 3.8)
                ))

    # 6. Update and Draw Lagrangian Particles with Additive Blending
    py5.blend_mode(py5.ADD)
    active_particles = []

    for p in particles:
        p.update()
        if not p.is_dead:
            active_particles.append(p)
            progress = p.life / p.max_life
            alpha = int(progress * 255)

            if p.ptype == "photon":
                # Cherenkov Scintillation: Electric cyan & radiant glacial blue (#38bdf8, #06b6d4)
                py5.no_stroke()
                py5.fill(6, 182, 212, int(alpha * 0.35))
                py5.circle(p.px, p.py, p.radius * 3.2)
                py5.fill(220, 248, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 0.9)
                py5.stroke(56, 189, 248, int(alpha * 0.75))
                py5.stroke_weight(1.2)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            elif p.ptype == "ion":
                # Ionization Wake Ember: Actinic ultraviolet & deep violet (#a855f7, #4f46e5)
                py5.no_stroke()
                py5.fill(124, 58, 237, int(alpha * 0.28))
                py5.circle(p.px, p.py, p.radius * 2.8)
                py5.fill(168, 85, 247, alpha)
                py5.circle(p.px, p.py, p.radius * 0.85)

            elif p.ptype == "delta":
                # Delta-Ray Cascade: Incandescent diamond-white and bremsstrahlung gold (#fef08a)
                py5.no_stroke()
                py5.fill(254, 240, 138, int(alpha * 0.45))
                py5.circle(p.px, p.py, p.radius * 3.5)
                py5.fill(255, 255, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 1.1)
                py5.stroke(254, 240, 138, int(alpha * 0.85))
                py5.stroke_weight(1.8)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

    particles = active_particles

    # 7. Render Primary Relativistic Lepton Head: Blinding Incandescent Diamond-White Core
    py5.no_stroke()
    # Outer halo (electric cyan)
    py5.fill(6, 182, 212, 45)
    py5.circle(screen_px, screen_py, 64.0)
    # Mid glow (actinic violet)
    py5.fill(124, 58, 237, 90)
    py5.circle(screen_px, screen_py, 36.0)
    # Inner incandescent core (diamond white)
    py5.fill(255, 255, 255, 245)
    py5.circle(screen_px, screen_py, 16.0)
    py5.fill(254, 240, 138, 220)
    py5.circle(screen_px, screen_py, 8.0)

    py5.blend_mode(py5.BLEND)

    # 8. Fail-safe: Blank screen detection
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # 9. Save animation frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        progress_pct = (py5.frame_count / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Particles: {len(particles)}")

    # 10. Finalize render on completion
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


if __name__ == "__main__":
    py5.run_sketch()

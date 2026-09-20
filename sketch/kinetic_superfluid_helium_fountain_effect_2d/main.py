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

# Spatial Simulation Grid (16:9 aspect ratio, 800x450 grid)
# Physical domain: x in [-4.0, 4.0], y in [-2.25, 2.25]
# In physical space: y = -2.25 is bottom, y = +2.25 is top.
Nx, Ny = 800, 450
x_coords = np.linspace(-4.0, 4.0, Nx, dtype=np.float32)
y_coords = np.linspace(-2.25, 2.25, Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
dx = float(x_coords[1] - x_coords[0])
dy = float(y_coords[1] - y_coords[0])

# Superfluid Helium-II Thermomechanical Fountain Geometry
NOZZLE_X = 0.0
NOZZLE_Y = -1.40  # Deep near the bottom of the physical domain

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Dual Light Vectors for Specular Liquid Chrome and Thermal Shading
light1 = np.array([0.55, -0.65, 0.52], dtype=np.float32)
light1 /= np.linalg.norm(light1)
light2 = np.array([-0.50, 0.60, 0.62], dtype=np.float32)
light2 /= np.linalg.norm(light2)
view_vec = np.array([0.0, 0.0, 1.0], dtype=np.float32)
h1 = (light1 + view_vec) / np.linalg.norm(light1 + view_vec)
h2 = (light2 + view_vec) / np.linalg.norm(light2 + view_vec)

# Lagrangian Particles: Ballistic Superfluid Droplets, Thermal Excitations & Vortex Pearls
MAX_PARTICLES = 1600
particles = []


class SuperfluidPearl:
    def __init__(self, px, py, ptype="droplet", vx=0.0, vy=0.0, life=130.0, radius=2.2):
        self.px = px
        self.py = py
        self.prev_x = px
        self.prev_y = py
        self.ptype = ptype  # "droplet", "thermal", "vortex"
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.radius = radius

    def update(self, dt=1.0):
        self.prev_x = self.px
        self.prev_y = self.py

        if self.ptype == "droplet":
            # Parabolic gravity trajectory (+y is downwards in screen coordinates)
            self.px += self.vx * dt
            self.py += self.vy * dt
            self.vy += 0.16 * dt  # Gravity pulls downward back to bath
            self.vx *= 0.998
        elif self.ptype == "thermal":
            # Thermal phonon-roton jitter rising upward from superleak base (-y is upward)
            self.px += (self.vx + random.uniform(-0.5, 0.5)) * dt
            self.py += (self.vy - random.uniform(0.5, 1.8)) * dt
            self.vx *= 0.92
            self.vy *= 0.92
        elif self.ptype == "vortex":
            # Quantized vortex tracer looping along fountain umbrella
            self.px += self.vx * dt
            self.py += self.vy * dt
            self.vy += 0.08 * dt
            self.vx *= 0.994

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


def compute_superfluid_fields(frame):
    """
    Synthesizes the macroscopic quantum fields of the Liquid Helium-II fountain:
    - Vertical fountain geyser erupting UPWARD from the superleak nozzle (from NOZZLE_Y up to crest_y)
    - Second sound (entropy/temperature) concentric wave oscillations
    - Parabolic ballistic umbrella curtains arching outward and falling back down
    - Rollin creeping film along container walls
    - 3D Blinn-Phong specular liquid chrome and thermal infrared normal shading
    """
    t = frame * 0.035
    t_norm = frame / TOTAL_FRAMES

    # 1. Fountain Geyser Height & Pulsation (in physical units)
    # Erupting from NOZZLE_Y (-1.40) upward to crest_y (+0.8 to +1.3)
    h_fountain = 2.45 + 0.35 * np.sin(t * 1.5) + 0.15 * np.cos(t * 3.0)
    crest_y = NOZZLE_Y + h_fountain  # Crest is in upper region of domain

    # 2. Central Geyser Column (Vertical Plume rising from nozzle to crest)
    dy_from_nozzle = Y_grid - NOZZLE_Y
    # Smooth sigmoid envelope starting at nozzle and extending to crest
    sigmoid_bottom = 1.0 / (1.0 + np.exp(-dy_from_nozzle * 8.0))
    sigmoid_crest = 1.0 / (1.0 + np.exp((Y_grid - (crest_y + 0.15)) * 6.0))
    
    # Core nozzle jet expands slightly as it rises
    height_ratio = np.clip(dy_from_nozzle / (h_fountain + 1e-4), 0.0, 1.2)
    width_column = 0.10 + 0.26 * (height_ratio**1.3)
    dist_to_center = np.abs(X_grid - NOZZLE_X)
    jet_core = (
        np.exp(- (dist_to_center / (width_column + 0.01))**2)
        * sigmoid_bottom
        * sigmoid_crest
    )

    # 3. Parabolic Ballistic Umbrella Curtains (Arching outward and falling down)
    # Target parabola: Y = crest_y - a * X^2
    umbrella_field = np.zeros_like(X_grid)
    for strand_i, a_curv in enumerate([0.35, 0.52, 0.78, 1.10]):
        phase_strand = t * 2.2 + strand_i * 1.2
        target_y = crest_y - a_curv * (X_grid**2) + 0.05 * np.sin(X_grid * 5.5 + phase_strand)
        dist_umbrella = np.abs(Y_grid - target_y)
        strand_w = 0.06 + 0.04 * np.abs(X_grid)
        # Umbrella only exists below the crest and decays smoothly outward
        exist_strand = 1.0 / (1.0 + np.exp((Y_grid - (crest_y + 0.1)) * 5.0))
        exist_strand *= 1.0 / (1.0 + np.exp(- (Y_grid - (NOZZLE_Y - 0.4)) * 4.0))
        strand_envelope = np.exp(- (dist_umbrella / strand_w)**2) * exist_strand
        umbrella_field += strand_envelope * (1.0 / (1.0 + 0.22 * np.abs(X_grid)))

    # 4. Thermal Second Sound Waves (Entropy/Temperature Ripples in the liquid bath)
    r_nozzle = np.sqrt((X_grid - NOZZLE_X)**2 + (Y_grid - NOZZLE_Y)**2)
    k_sound = 12.0
    omega_sound = 4.2
    # Second sound ripples radiating outward through the cryostat
    bath_mask = 1.0 / (1.0 + np.exp((Y_grid - (NOZZLE_Y + 0.4)) * 3.5))
    second_sound = (
        np.cos(k_sound * r_nozzle - omega_sound * t)
        * np.exp(-r_nozzle * 0.9)
        * bath_mask
    )

    # 5. Rollin Creeping Film Flow (Macroscopic Quantum Capillarity along Cryostat Walls)
    dist_wall_left = np.abs(X_grid - (-3.35))
    dist_wall_right = np.abs(X_grid - (3.35))
    wall_profile = (
        np.exp(- (dist_wall_left / 0.12)**2) + np.exp(- (dist_wall_right / 0.12)**2)
    ) * (1.0 / (1.0 + np.exp(- (Y_grid - NOZZLE_Y + 0.2) * 3.0)))
    # Periodic quantum pearls dripping along the wall
    film_droplets = (
        (np.cos(Y_grid * 14.0 + t * 2.8)**4)
        * (np.exp(-dist_wall_left / 0.18) + np.exp(-dist_wall_right / 0.18))
    )

    # 6. Superleak Porous Plug Base Glow (Thermal Infrared Origin)
    r_plug_sq = (X_grid - NOZZLE_X)**2 / 0.35 + (Y_grid - NOZZLE_Y)**2 / 0.10
    thermal_plug_glow = np.exp(-r_plug_sq) * 3.5

    # 7. Total Cryogenic Fluid Intensity Field
    I_fluid = (
        jet_core * 1.6
        + umbrella_field * 0.95
        + second_sound * 0.35
        + wall_profile * 0.75
        + film_droplets * 0.50
    )

    # 8. 3D Blinn-Phong Specular Liquid Chrome Normal Shading
    H_surf = np.sqrt(np.clip(I_fluid, 0.0, 4.0)) * 0.55
    grad_H_y, grad_H_x = np.gradient(H_surf, dy, dx)
    norm_denom = np.sqrt(grad_H_x**2 + grad_H_y**2 + 1.0)
    Nx_s = -grad_H_x / norm_denom
    Ny_s = -grad_H_y / norm_denom
    Nz_s = 1.0 / norm_denom

    spec1 = np.maximum(0.0, Nx_s * h1[0] + Ny_s * h1[1] + Nz_s * h1[2])**20
    spec2 = np.maximum(0.0, Nx_s * h2[0] + Ny_s * h2[1] + Nz_s * h2[2])**14

    return (
        I_fluid,
        jet_core,
        umbrella_field,
        second_sound,
        thermal_plug_glow,
        spec1,
        spec2,
        crest_y,
        t,
    )


def render_superfluid_canvas(
    I_fluid,
    jet_core,
    umbrella_field,
    second_sound,
    thermal_plug_glow,
    spec1,
    spec2,
):
    """
    Renders 4-channel image into pixel_buffer following 60-30-10 palette rules:
    - 60% Sub-Kelvin Liquid Void Obsidian & Indigo Abyss (#01030a, #060b1e)
    - 30% Superfluid Helium Plume Electric Cyan & Glacial Azure (#06b6d4, #38bdf8, #0284c7)
    - 10% Thermal Infrared Superleak Amber (#f59e0b) & Crest Diamond-White (#ffffff)
    """
    # 1. Background 60%: Cryogenic sub-Kelvin vacuum with smooth radial gradient
    r_bg = 1.5 + np.exp(- (X_grid**2 + (Y_grid + 0.5)**2) / 8.0) * 3.0
    g_bg = 3.0 + np.exp(- (X_grid**2 + (Y_grid + 0.5)**2) / 8.0) * 6.0
    b_bg = 10.0 + np.exp(- (X_grid**2 + (Y_grid + 0.5)**2) / 8.0) * 22.0

    # 2. Dominant & Secondary 30%: Liquid Helium Electric Cyan & Glacial Azure
    cyan_stream = np.clip((jet_core * 1.25 + umbrella_field * 0.95), 0.0, 2.5)
    r_cyan = cyan_stream * 6.0 + np.maximum(0.0, second_sound) * 14.0
    g_cyan = cyan_stream * 182.0 + np.maximum(0.0, second_sound) * 110.0
    b_cyan = cyan_stream * 212.0 + np.maximum(0.0, second_sound) * 240.0

    # Specular liquid chrome reflections
    spec_r = spec1 * 140.0 + spec2 * 245.0
    spec_g = spec1 * 220.0 + spec2 * 190.0
    spec_b = spec1 * 255.0 + spec2 * 70.0

    r_fluid = r_cyan * 0.70 + spec_r * 0.40
    g_fluid = g_cyan * 0.75 + spec_g * 0.40
    b_fluid = b_cyan * 0.85 + spec_b * 0.40

    blend_factor = np.clip(I_fluid * 0.85, 0.0, 1.0)
    r_mid = r_bg * (1.0 - blend_factor) + r_fluid * blend_factor
    g_mid = g_bg * (1.0 - blend_factor) + g_fluid * blend_factor
    b_mid = b_bg * (1.0 - blend_factor) + b_fluid * blend_factor

    # 3. Accent 10%: Thermal Infrared Superleak Amber (#f59e0b) & Crest Diamond-White (#ffffff)
    r_thermal = thermal_plug_glow * 245.0
    g_thermal = thermal_plug_glow * 158.0
    b_thermal = thermal_plug_glow * 11.0

    crest_accent = np.clip((jet_core * umbrella_field)**1.1 * 1.9 + spec1 * 0.45, 0.0, 2.0)
    r_crest = crest_accent * 255.0
    g_crest = crest_accent * 250.0
    b_crest = crest_accent * 255.0

    # Final pixel buffer compilation clamped to uint8
    r_final = np.clip(r_mid + r_thermal + r_crest, 0.0, 255.0).astype(np.uint8)
    g_final = np.clip(g_mid + g_thermal + g_crest, 0.0, 255.0).astype(np.uint8)
    b_final = np.clip(b_mid + b_thermal + b_crest, 0.0, 255.0).astype(np.uint8)

    # Note on orientation: In NumPy, index 0 is row 0.
    # In physical space, Y_grid goes from y_coords[0] = -2.25 (row 0) to y_coords[-1] = +2.25 (row -1).
    # To map physical +Y to screen UPWARD (-y in screen space), row 0 should be top (+2.25) and row -1 bottom (-2.25).
    # We flip vertically along axis 0 so that row 0 corresponds to +Y (top of canvas):
    pixel_buffer[..., 1] = np.flipud(r_final)
    pixel_buffer[..., 2] = np.flipud(g_final)
    pixel_buffer[..., 3] = np.flipud(b_final)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw_frame():
    global particles

    # 1. Compute superfluid fountain fields
    (
        I_fluid,
        jet_core,
        umbrella_field,
        second_sound,
        thermal_plug_glow,
        spec1,
        spec2,
        crest_y,
        t,
    ) = compute_superfluid_fields(py5.frame_count)

    # 2. Render pixel buffer canvas (with flipud so nozzle is at bottom and crest at top)
    render_superfluid_canvas(
        I_fluid,
        jet_core,
        umbrella_field,
        second_sound,
        thermal_plug_glow,
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

    # 4. Map physical simulation coordinates to screen space (with inverted Y so +Y is UP)
    # Screen X: x_coords[0] -> 0, x_coords[-1] -> width
    # Screen Y: y_coords[-1] (+2.25, top) -> 0, y_coords[0] (-2.25, bottom) -> height
    y_min, y_max = y_coords[0], y_coords[-1]
    nozzle_screen_x = (NOZZLE_X - x_coords[0]) / (x_coords[-1] - x_coords[0]) * py5.width
    nozzle_screen_y = (1.0 - (NOZZLE_Y - y_min) / (y_max - y_min)) * py5.height
    crest_screen_y = (1.0 - (crest_y - y_min) / (y_max - y_min)) * py5.height

    # 5. Spawn Lagrangian Quantum Particles
    if len(particles) < MAX_PARTICLES:
        spawn_n = min(45, MAX_PARTICLES - len(particles))
        for _ in range(spawn_n):
            roll = random.random()

            if roll < 0.65:
                # Ballistic Helium Pearls: Shedding from the fountain umbrella crest
                # Launching symmetrically outward and arching DOWNWARD under gravity
                side = 1.0 if random.random() < 0.5 else -1.0
                vx = side * random.uniform(2.0, 7.2) + random.gauss(0.0, 0.4)
                vy = -random.uniform(0.5, 3.8)  # Initial upward velocity in screen coords (towards 0)
                spawn_x = nozzle_screen_x + side * random.uniform(4.0, 60.0)
                spawn_y = crest_screen_y + random.uniform(-10.0, 20.0)
                particles.append(SuperfluidPearl(
                    spawn_x,
                    spawn_y,
                    ptype="droplet",
                    vx=vx,
                    vy=vy,
                    life=random.uniform(70.0, 140.0),
                    radius=random.uniform(1.4, 3.2)
                ))

            elif roll < 0.85:
                # Thermal Phonon-Roton Sparks: Rising upward from the heated superleak nozzle
                spawn_x = nozzle_screen_x + random.gauss(0.0, 22.0)
                spawn_y = nozzle_screen_y + random.gauss(0.0, 8.0)
                particles.append(SuperfluidPearl(
                    spawn_x,
                    spawn_y,
                    ptype="thermal",
                    vx=random.uniform(-1.0, 1.0),
                    vy=-random.uniform(1.5, 4.5),  # Rising upward in screen space
                    life=random.uniform(40.0, 95.0),
                    radius=random.uniform(1.8, 3.6)
                ))

            else:
                # Quantized Vortex Filaments: Swirling in the fountain core
                y_pos = random.uniform(crest_screen_y, nozzle_screen_y)
                spawn_x = nozzle_screen_x + random.gauss(0.0, 30.0)
                particles.append(SuperfluidPearl(
                    spawn_x,
                    y_pos,
                    ptype="vortex",
                    vx=random.uniform(-2.5, 2.5),
                    vy=-random.uniform(2.0, 5.5),
                    life=random.uniform(50.0, 100.0),
                    radius=random.uniform(1.2, 2.4)
                ))

    # 6. Update and Draw Particles with Additive Blending
    py5.blend_mode(py5.ADD)
    active_particles = []

    for p in particles:
        p.update()
        if not p.is_dead:
            active_particles.append(p)
            progress = p.life / p.max_life
            alpha = int(progress * 255)

            if p.ptype == "droplet":
                # Ballistic helium droplet: Electric cyan and glacial white (#06b6d4, #ffffff)
                py5.no_stroke()
                py5.fill(6, 182, 212, int(alpha * 0.38))
                py5.circle(p.px, p.py, p.radius * 3.4)
                py5.fill(240, 252, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 0.95)
                py5.stroke(56, 189, 248, int(alpha * 0.75))
                py5.stroke_weight(1.3)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            elif p.ptype == "thermal":
                # Thermal phonon excitation: Molten amber & solar gold (#f59e0b, #d97706)
                py5.no_stroke()
                py5.fill(245, 158, 11, int(alpha * 0.45))
                py5.circle(p.px, p.py, p.radius * 3.2)
                py5.fill(254, 240, 138, alpha)
                py5.circle(p.px, p.py, p.radius * 1.0)
                py5.stroke(217, 119, 6, int(alpha * 0.80))
                py5.stroke_weight(1.6)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            elif p.ptype == "vortex":
                # Quantized vortex loop: Electric amethyst & violet (#c084fc, #a855f7)
                py5.no_stroke()
                py5.fill(192, 132, 252, int(alpha * 0.35))
                py5.circle(p.px, p.py, p.radius * 2.8)
                py5.fill(235, 215, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 0.85)

    particles = active_particles

    # 7. Render Superleak Nozzle & Fountain Crest Nodes
    py5.no_stroke()
    # Thermal superleak heating aura at the base
    py5.fill(245, 158, 11, 65)
    py5.circle(nozzle_screen_x, nozzle_screen_y, 80.0)
    py5.fill(217, 119, 6, 125)
    py5.circle(nozzle_screen_x, nozzle_screen_y, 45.0)
    py5.fill(254, 240, 138, 225)
    py5.circle(nozzle_screen_x, nozzle_screen_y, 18.0)

    # Incandescent crest focal point at the top
    py5.fill(6, 182, 212, 55)
    py5.circle(nozzle_screen_x, crest_screen_y, 65.0)
    py5.fill(255, 255, 255, 235)
    py5.circle(nozzle_screen_x, crest_screen_y, 16.0)

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
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Pearls: {len(particles)}")

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

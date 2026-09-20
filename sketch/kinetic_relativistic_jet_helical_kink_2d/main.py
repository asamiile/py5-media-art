"""
kinetic_relativistic_jet_helical_kink_2d
Astrophysical relativistic magnetohydrodynamic simulation of the m=1 helical kink instability
in an extragalactic plasma jet: current-driven Kruskal-Shafranov threshold collapse,
relativistic Doppler beaming asymmetry, internal recollimation shock diamonds,
braided helical magnetic flux ropes, and Lagrangian synchrotron lepton kinematics.

1920x1080 / 3840x2160 @ 60fps, 900 frames (15 seconds).
"""

from pathlib import Path
import os
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
Nx, Ny = 800, 450
x_coords = np.linspace(-4.0, 4.0, Nx, dtype=np.float32)
y_coords = np.linspace(-2.25, 2.25, Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
dx = float(x_coords[1] - x_coords[0])
dy = float(y_coords[1] - y_coords[0])

# Dual Specular Light Vectors for Relativistic Plasma Chrome Shading
light1 = np.array([0.55, -0.65, 0.52], dtype=np.float32)
light1 /= np.linalg.norm(light1)
light2 = np.array([-0.50, 0.60, 0.62], dtype=np.float32)
light2 /= np.linalg.norm(light2)
view_vec = np.array([0.0, 0.0, 1.0], dtype=np.float32)
h1 = (light1 + view_vec) / np.linalg.norm(light1 + view_vec)
h2 = (light2 + view_vec) / np.linalg.norm(light2 + view_vec)

# ARGB pixel buffer for py5 (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Physical Parameters of the Relativistic Helical Jet
JET_RADIUS = 0.32          # Unperturbed jet column radius
BETA_BULK = 0.94           # Relativistic bulk flow velocity v/c
GAMMA_LORENTZ = 1.0 / np.sqrt(1.0 - BETA_BULK**2)  # Lorentz factor ~ 2.93
K_KINK = 2.4               # Helical spatial wavenumber
OMEGA_KINK = 2.2           # Helical rotation frequency


class SynchrotronParticle:
    """Lagrangian particle representing a relativistic lepton spiraling in the helical magnetic field."""
    def __init__(self, x, y, ptype="lepton", vx=0.0, vy=0.0, life=60.0, radius=2.0):
        self.x = float(x)
        self.y = float(y)
        self.ptype = ptype
        self.vx = float(vx)
        self.vy = float(vy)
        self.life = float(life)
        self.max_life = float(life)
        self.radius = float(radius)
        self.is_dead = False
        self.history = []

    def update(self):
        self.life -= 1.0
        if self.life <= 0.0:
            self.is_dead = True
            return

        self.history.append((self.x, self.y))
        if len(self.history) > 6:
            self.history.pop(0)

        if self.ptype == "lepton":
            # High-velocity relativistic forward advection with helical gyrating motion
            self.x += self.vx
            self.y += self.vy
        elif self.ptype == "shock_spark":
            # Explosive burst from recollimation shock diamond
            self.vx *= 0.93
            self.vy *= 0.93
            self.x += self.vx
            self.y += self.vy
        elif self.ptype == "cocoon":
            # Turbulent eddy tracer in the outer plasma cocoon
            self.vx = 0.9 * self.vx + 0.1 * random.uniform(-0.5, 0.5)
            self.vy = 0.9 * self.vy + 0.1 * random.uniform(-0.8, 0.8)
            self.x += self.vx
            self.y += self.vy

    def draw(self, w, h):
        alpha_frac = max(0.0, min(1.0, self.life / self.max_life))
        pulse = 0.7 + 0.3 * np.sin(self.life * 0.3)

        if self.ptype == "lepton":
            # Electric cyan / glacial azure synchrotron tracer
            col_a = int(alpha_frac * 220 * pulse)
            py5.stroke(50, 225, 255, col_a)
            py5.stroke_weight(self.radius * (0.8 + 0.4 * alpha_frac))
            py5.point(self.x, self.y)

            if len(self.history) > 1:
                py5.stroke(25, 140, 255, int(col_a * 0.5))
                py5.stroke_weight(max(1.0, self.radius * 0.6))
                hx, hy = self.history[-2]
                py5.line(hx, hy, self.x, self.y)

        elif self.ptype == "shock_spark":
            # Incandescent diamond-white / solar platinum shock flare spark
            col_a = int(alpha_frac * 255)
            glow_r = self.radius * (1.6 + (1.0 - alpha_frac) * 2.2)
            py5.no_stroke()
            py5.fill(255, 255, 255, col_a)
            py5.ellipse(self.x, self.y, glow_r * 0.8, glow_r * 0.8)
            py5.fill(255, 220, 140, int(col_a * 0.7))
            py5.ellipse(self.x, self.y, glow_r * 2.0, glow_r * 2.0)

        elif self.ptype == "cocoon":
            # Warm amber / copper turbulent eddy tracer
            col_a = int(alpha_frac * 170)
            py5.stroke(255, 145, 45, col_a)
            py5.stroke_weight(self.radius * 0.8)
            py5.point(self.x, self.y)
            if len(self.history) > 1:
                py5.stroke(215, 80, 25, int(col_a * 0.45))
                py5.stroke_weight(self.radius * 0.45)
                hx, hy = self.history[-2]
                py5.line(hx, hy, self.x, self.y)


particles = []
MAX_PARTICLES = 1400


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    py5.background(2, 4, 10)


def compute_helical_jet_state(t, frame_idx):
    """
    Computes the relativistic 3D helical kink magnetohydrodynamic state projected onto 2D:
    - Current-driven helical spine displacement (Y_spine, Z_spine)
    - Relativistic Doppler beaming amplification on approaching helical coils
    - Internal recollimation shock diamond knots
    - Braided helical magnetic flux rope coils
    - Turbulent plasma cocoon envelope
    """
    # 1. Helical Kink Spine Profile
    # The kink instability develops spatially along x, growing as the current builds up
    spatial_growth = 0.55 / (1.0 + np.exp(-1.5 * (X_grid + 1.2)))
    # Time-dependent breathing of the kink mode
    kink_phase = K_KINK * X_grid - OMEGA_KINK * t

    # Projected transverse position Y_spine and line-of-sight depth Z_spine
    Y_spine = spatial_growth * np.sin(kink_phase)
    Z_spine = spatial_growth * np.cos(kink_phase)

    # Line-of-sight velocity component for Doppler boosting
    # d(Z_spine)/dt = OMEGA_KINK * spatial_growth * np.sin(kink_phase)
    # Plus bulk velocity component along jet projected by kink angle
    dZ_dt = OMEGA_KINK * spatial_growth * np.sin(kink_phase)
    # Cosine of angle to observer (z-axis): cos(theta) ~ dZ_dt / c
    cos_theta = np.clip(dZ_dt / 2.0, -0.9, 0.9)

    # Relativistic Doppler Boosting factor delta = 1 / [GAMMA * (1 - beta * cos_theta)]
    doppler_factor = 1.0 / (GAMMA_LORENTZ * np.maximum(0.12, 1.0 - BETA_BULK * cos_theta))
    # Beaming intensity enhancement ~ delta^3
    doppler_boost = np.clip(doppler_factor**3.0, 0.15, 8.5)

    # 2. Distance to the Deformed Jet Spine
    dist_to_spine = np.sqrt((Y_grid - Y_spine)**2)

    # Core jet column profile
    jet_core_density = np.exp(-(dist_to_spine / JET_RADIUS)**2)

    # Braided helical magnetic flux rope coils wrapping around spine
    braid_k = 7.5
    braid_phase = braid_k * X_grid + 3.0 * np.arctan2(Y_grid - Y_spine, Z_spine) - 5.0 * t
    braid_coils = 0.45 * np.cos(braid_phase)**2 * np.exp(-(dist_to_spine / (JET_RADIUS * 1.8))**2)

    # 3. Internal Recollimation Shock Diamonds (Mach Knots)
    # Shock diamonds form at periodic pinch points along the jet axis
    shock_period = 1.35
    dist_to_knots = np.abs((X_grid - 0.5 * t) % shock_period - (shock_period * 0.5))
    shock_knots = np.exp(-(dist_to_knots / 0.12)**2) * np.exp(-(dist_to_spine / (JET_RADIUS * 0.75))**2)

    # 4. Outer Plasma Cocoon & Bow Shock Turbulent Sheath
    # As the jet corkscrews, it sweeps up ambient gas into an expanding turbulent cocoon
    cocoon_radius = 0.85 + 0.28 * np.maximum(0.0, X_grid + 3.0)**0.65
    cocoon_edge = np.exp(-((dist_to_spine - cocoon_radius) / 0.25)**2)

    # Turbulent eddy perturbations in the cocoon
    eddy_turb = 0.25 * np.sin(5.0 * X_grid + 3.0 * Y_grid - 2.0 * t) * \
                0.25 * np.sin(3.5 * X_grid - 4.2 * Y_grid + 1.5 * t)
    cocoon_field = np.where(dist_to_spine < cocoon_radius * 1.4, (cocoon_edge + eddy_turb) * 0.65, 0.0)

    # 5. Combined Relativistic Synchrotron Optical Density Field
    synchrotron_field = (
        jet_core_density * doppler_boost +
        braid_coils * 1.4 +
        shock_knots * 2.8 +
        cocoon_field * 0.6
    )

    # 6. Surface Normal Calculation for 3D Chrome Shading
    grad_y, grad_x = np.gradient(synchrotron_field, dy, dx)
    inv_norm = 1.0 / np.sqrt(grad_x**2 + grad_y**2 + 1.0)
    nx_map = -grad_x * inv_norm
    ny_map = -grad_y * inv_norm
    nz_map = inv_norm

    # 7. Specular Highlights (Blinn-Phong)
    ndoth1 = np.maximum(0.0, nx_map * h1[0] + ny_map * h1[1] + nz_map * h1[2])
    ndoth2 = np.maximum(0.0, nx_map * h2[0] + ny_map * h2[1] + nz_map * h2[2])
    specular1 = ndoth1**36.0
    specular2 = ndoth2**48.0

    # 8. Diffuse Illuminations
    diffuse1 = np.maximum(0.0, nx_map * light1[0] + ny_map * light1[1] + nz_map * light1[2])
    diffuse2 = np.maximum(0.0, nx_map * light2[0] + ny_map * light2[1] + nz_map * light2[2])

    return (
        jet_core_density,
        doppler_boost,
        braid_coils,
        shock_knots,
        cocoon_field,
        diffuse1,
        diffuse2,
        specular1,
        specular2,
        Y_spine,
        spatial_growth
    )


def render_field_to_buffer(
    jet_core_density,
    doppler_boost,
    braid_coils,
    shock_knots,
    cocoon_field,
    diffuse1,
    diffuse2,
    specular1,
    specular2
):
    """
    Composes the relativistic astrophysical color palette into the ARGB pixel buffer:
    - Background: Extragalactic cosmic vacuum abyss (#02040a)
    - Dominant: Doppler-boosted approaching jet spine in electric glacial cyan (#30d5f8) and luminous sapphire
    - Secondary: Receding cocoon plasma and braided flux ropes in incandescent amber (#ff9820), solar gold, and copper
    - Accent: Internal recollimation shock diamonds in diamond-white (#ffffff) and solar platinum
    """
    # Base background: Deep cosmic void
    r_field = np.full((Ny, Nx), 2.0, dtype=np.float32)
    g_field = np.full((Ny, Nx), 4.0, dtype=np.float32)
    b_field = np.full((Ny, Nx), 10.0, dtype=np.float32)

    # Ambient extragalactic diffuse glow
    dist_c = np.sqrt(X_grid**2 + Y_grid**2)
    ambient_glow = np.exp(-dist_c * 0.3) * 12.0
    r_field += ambient_glow * 0.4
    g_field += ambient_glow * 0.6
    b_field += ambient_glow * 1.5

    # Relativistic Jet Core: modulated by Doppler boost
    # Approaching portions (boosted) glow brilliant electric cyan/azure;
    # Receding portions glow deep amber/copper
    core_norm = np.clip(jet_core_density * 1.4, 0.0, 1.8)
    boost_norm = np.clip(doppler_boost / 4.0, 0.0, 2.0)

    # Electric Cyan & Sapphire Beaming
    cyan_r = core_norm * (35.0 + 30.0 * diffuse2) * boost_norm
    cyan_g = core_norm * (180.0 + 60.0 * diffuse2) * boost_norm
    cyan_b = core_norm * (255.0 + 40.0 * diffuse2) * boost_norm
    r_field += cyan_r
    g_field += cyan_g
    b_field += cyan_b

    # Braided Magnetic Flux Ropes (Incandescent Amber & Solar Gold)
    braid_norm = np.maximum(0.0, braid_coils)
    r_field += braid_norm * (255.0 + 40.0 * diffuse1)
    g_field += braid_norm * (150.0 + 30.0 * diffuse1)
    b_field += braid_norm * 30.0

    # Cocoon Plasma (Deep Copper & Warm Sienna)
    coc_norm = np.maximum(0.0, cocoon_field)
    r_field += coc_norm * 180.0
    g_field += coc_norm * 85.0
    b_field += coc_norm * 25.0

    # Internal Recollimation Shock Diamonds (Blinding Synchrotron Diamond-White)
    shock_norm = np.clip(shock_knots * 2.5, 0.0, 3.0)
    r_field += shock_norm * 255.0
    g_field += shock_norm * 248.0
    b_field += shock_norm * 230.0

    # Specular High-Energy Chrome Highlights
    spec_total = specular1 * 1.15 + specular2 * 0.95
    r_field += spec_total * 255.0
    g_field += spec_total * 250.0
    b_field += spec_total * 240.0

    # Final Clipping and Transfer to Buffer
    pixel_buffer[..., 1] = np.clip(r_field, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g_field, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b_field, 0, 255).astype(np.uint8)


def draw_frame():
    frame = py5.frame_count
    t = float(frame) / float(FPS)

    # 1. Compute Continuum Relativistic Helical Jet State
    (
        jet_core_density,
        doppler_boost,
        braid_coils,
        shock_knots,
        cocoon_field,
        diffuse1,
        diffuse2,
        specular1,
        specular2,
        Y_spine,
        spatial_growth
    ) = compute_helical_jet_state(t, frame)

    # 2. Render Continuum Fields to High-Precision ARGB Pixel Buffer
    render_field_to_buffer(
        jet_core_density,
        doppler_boost,
        braid_coils,
        shock_knots,
        cocoon_field,
        diffuse1,
        diffuse2,
        specular1,
        specular2
    )

    # 3. Blit Buffer to 4K Canvas
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

    # 4. Lagrangian Particle Dynamics (Synchrotron Leptons, Shock Flare Sparks, Cocoon Eddies)
    def sim_to_screen(sx, sy):
        px = (sx - x_coords[0]) / (x_coords[-1] - x_coords[0]) * py5.width
        py = (y_coords[-1] - sy) / (y_coords[-1] - y_coords[0]) * py5.height
        return px, py

    # Spawn particles dynamically
    if len(particles) < MAX_PARTICLES and frame < TOTAL_FRAMES - 30:
        spawn_budget = min(45, MAX_PARTICLES - len(particles))
        for _ in range(spawn_budget):
            roll = random.random()

            if roll < 0.45:
                # Relativistic lepton racing forward along helical spine
                x_sample_idx = random.randint(10, Nx - 11)
                sim_x = float(x_coords[x_sample_idx])
                spine_y = float(Y_spine[Ny // 2, x_sample_idx])
                sim_y = spine_y + random.gauss(0.0, JET_RADIUS * 0.8)
                px, py = sim_to_screen(sim_x, sim_y)

                # Fast relativistic forward velocity
                particles.append(SynchrotronParticle(
                    px, py,
                    ptype="lepton",
                    vx=random.uniform(5.5, 11.0),
                    vy=random.gauss(0.0, 1.2),
                    life=random.uniform(35.0, 75.0),
                    radius=random.uniform(1.4, 2.6)
                ))

            elif roll < 0.75:
                # Shock flare spark burst at recollimation shock pinch nodes
                knot_x = -2.5 + ((random.random() * 6.0 + 0.5 * t) % 6.0)
                nearest_x_idx = int((knot_x - x_coords[0]) / dx)
                nearest_x_idx = max(0, min(Nx - 1, nearest_x_idx))
                spine_y = float(Y_spine[Ny // 2, nearest_x_idx])
                px, py = sim_to_screen(knot_x, spine_y)

                spark_speed = random.uniform(4.5, 9.5)
                spark_ang = random.uniform(-np.pi, np.pi)
                particles.append(SynchrotronParticle(
                    px, py,
                    ptype="shock_spark",
                    vx=spark_speed * np.cos(spark_ang),
                    vy=spark_speed * np.sin(spark_ang),
                    life=random.uniform(20.0, 45.0),
                    radius=random.uniform(2.0, 4.0)
                ))

            else:
                # Cocoon turbulent eddy tracer
                sim_x = random.uniform(-3.5, 3.5)
                sim_y = random.choice([-1.0, 1.0]) * random.uniform(0.7, 1.8)
                px, py = sim_to_screen(sim_x, sim_y)
                particles.append(SynchrotronParticle(
                    px, py,
                    ptype="cocoon",
                    vx=random.uniform(1.0, 3.5),
                    vy=random.uniform(-1.0, 1.0),
                    life=random.uniform(45.0, 90.0),
                    radius=random.uniform(1.2, 2.2)
                ))

    # Update and Draw Lagrangian Particles with Additive Blending
    py5.blend_mode(py5.ADD)
    active_particles = []
    for p in particles:
        p.update()
        if not p.is_dead:
            p.draw(py5.width, py5.height)
            active_particles.append(p)
    particles[:] = active_particles
    py5.blend_mode(py5.BLEND)

    # 5. Save Frame for Video Compilation
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe blank screen check
    if frame == 2 or frame % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {frame} (std < 1.0). Aborting.")
            os._exit(1)

    # Progress feedback
    if frame % 60 == 0:
        progress_pct = (frame / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Max Doppler: {np.max(doppler_boost):.2f} | Particles: {len(particles)}")

    # 6. Video Compilation & Cleanup when Total Frames Reached
    if frame >= TOTAL_FRAMES:
        py5.exit_sketch()

        print("\n[Render Complete] Compiling H.264 video with FFmpeg...")
        mp4_path = SKETCH_DIR / f"{WORK_NAME}.mp4"
        output_mp4 = SKETCH_DIR / "output.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-preset", "medium",
            str(mp4_path)
        ]

        try:
            subprocess.run(cmd, check=True)
            print(f"[Video Compiled] Master MP4 saved: {mp4_path}")
            shutil.copyfile(mp4_path, output_mp4)
            print(f"[Video Copied] Duplicated to: {output_mp4}")
        except subprocess.CalledProcessError as e:
            print(f"[FFmpeg Error] Failed to encode video: {e}")
            sys.exit(1)

        # Save midpoint preview frame
        midpoint_frame = FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png"
        if midpoint_frame.exists():
            shutil.copyfile(midpoint_frame, SKETCH_DIR / PREVIEW_FILENAME)
            print(f"[Preview Saved] Saved preview image: {SKETCH_DIR / PREVIEW_FILENAME}")
        else:
            last_frame = FRAMES_DIR / f"frame-{TOTAL_FRAMES:04d}.png"
            if last_frame.exists():
                shutil.copyfile(last_frame, SKETCH_DIR / PREVIEW_FILENAME)
                print(f"[Preview Saved] Saved fallback preview image: {SKETCH_DIR / PREVIEW_FILENAME}")

        # Clean up temporary frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.\n")

        os._exit(0)


def draw():
    try:
        draw_frame()
    except Exception:
        import traceback
        traceback.print_exc()
        os._exit(1)


if __name__ == "__main__":
    py5.run_sketch()

"""
kinetic_richtmyer_meshkov_shock_vortices_2d
Supersonic shock-interface hydrodynamic simulation of the Richtmyer-Meshkov Instability (RMI):
impulsive baroclinic vorticity deposition (grad rho x grad P), mushroom spike and bubble formation,
vortex sheet Biot-Savart roll-up, Mach diamond reflections, and Lagrangian aerosol tracer kinetics.

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

# Dual Specular Light Vectors for High-Energy Plasma & Fluid Chrome Shading
light1 = np.array([0.60, -0.65, 0.55], dtype=np.float32)
light1 /= np.linalg.norm(light1)
light2 = np.array([-0.55, 0.60, 0.65], dtype=np.float32)
light2 /= np.linalg.norm(light2)
view_vec = np.array([0.0, 0.0, 1.0], dtype=np.float32)
h1 = (light1 + view_vec) / np.linalg.norm(light1 + view_vec)
h2 = (light2 + view_vec) / np.linalg.norm(light2 + view_vec)

# ARGB pixel buffer for py5 (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Physical Parameters of the Richtmyer-Meshkov Interface
# Multi-mode corrugated interface parameters: initial position x_0 ≈ -1.8
X_INT_BASE = -1.8
MODES = [
    {"k": 1.4, "amp": 0.45, "phase": 0.0},
    {"k": 2.8, "amp": 0.18, "phase": 0.8},
    {"k": 4.2, "amp": 0.08, "phase": 2.1},
    {"k": 0.7, "amp": 0.20, "phase": -0.5},
]

# Shock Speed and Timeline
V_SHOCK = 0.55  # Shock velocity in x
T_SHOCK_START = -3.8  # Starting x position of shock at t=0


class AerosolParticle:
    """Lagrangian aerosol / ionization tracer particle entrained in vortex flow."""
    def __init__(self, x, y, ptype="soot", vx=0.0, vy=0.0, life=100.0, radius=2.0):
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

    def update(self, flow_vx, flow_vy):
        self.life -= 1.0
        if self.life <= 0.0:
            self.is_dead = True
            return

        # Particle dynamics with drag and inertia
        self.history.append((self.x, self.y))
        if len(self.history) > 6:
            self.history.pop(0)

        if self.ptype == "soot":
            # Advected strongly by the fluid velocity
            self.vx = 0.82 * self.vx + 0.18 * flow_vx
            self.vy = 0.82 * self.vy + 0.18 * flow_vy
        elif self.ptype == "spark":
            # High-velocity energetic ejection with rapid deceleration
            self.vx *= 0.94
            self.vy *= 0.94
        elif self.ptype == "filament":
            self.vx = 0.75 * self.vx + 0.25 * flow_vx
            self.vy = 0.75 * self.vy + 0.25 * flow_vy

        self.x += self.vx
        self.y += self.vy

    def draw(self, w, h):
        alpha_frac = max(0.0, min(1.0, self.life / self.max_life))
        pulse = 0.7 + 0.3 * np.sin(self.life * 0.2)

        if self.ptype == "soot":
            # Luminous amber/copper aerosol ember
            col_a = int(alpha_frac * 200 * pulse)
            py5.stroke(255, 170, 70, col_a)
            py5.stroke_weight(self.radius * (0.8 + 0.4 * alpha_frac))
            py5.point(self.x, self.y)

            # Draw subtle trail
            if len(self.history) > 2:
                py5.no_fill()
                py5.stroke(240, 110, 40, int(col_a * 0.45))
                py5.stroke_weight(max(1.0, self.radius * 0.6))
                py5.begin_shape()
                for hx, hy in self.history:
                    py5.vertex(hx, hy)
                py5.end_shape()

        elif self.ptype == "spark":
            # Incandescent solar platinum / diamond-white shock triple-point spark
            col_a = int(alpha_frac * 255)
            glow_r = self.radius * (1.5 + (1.0 - alpha_frac) * 2.0)
            py5.no_stroke()
            py5.fill(255, 245, 220, col_a)
            py5.ellipse(self.x, self.y, glow_r * 0.8, glow_r * 0.8)
            py5.fill(160, 230, 255, int(col_a * 0.6))
            py5.ellipse(self.x, self.y, glow_r * 1.8, glow_r * 1.8)

        elif self.ptype == "filament":
            # Cyan/electric azure ionizing trail
            col_a = int(alpha_frac * 180 * pulse)
            py5.stroke(70, 210, 255, col_a)
            py5.stroke_weight(self.radius * 0.9)
            py5.point(self.x, self.y)
            if len(self.history) > 1:
                py5.stroke(40, 150, 240, int(col_a * 0.5))
                py5.stroke_weight(self.radius * 0.5)
                hx, hy = self.history[-2]
                py5.line(hx, hy, self.x, self.y)


particles = []
MAX_PARTICLES = 1200


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    py5.background(5, 7, 15)


def compute_simulation_state(t, frame_idx):
    """
    Computes the 2D compressible hydrodynamic fields of the Richtmyer-Meshkov Instability:
    - Planar incident and transmitted shock waves with Mach stem diamonds
    - Corrugated multi-mode density boundary with baroclinic roll-up
    - Vortex sheet roll-up into primary mushroom scrolls and secondary Kelvin-Helmholtz billows
    - Rarefaction waves, acoustic reverberation caustics, and specular lighting
    """
    # 1. Shock Position
    x_shock = T_SHOCK_START + V_SHOCK * t

    # 2. Initial Corrugated Interface Shape
    y_profile = np.zeros_like(Y_grid)
    for m in MODES:
        y_profile += m["amp"] * np.cos(m["k"] * Y_grid + m["phase"])

    x_interface_0 = X_INT_BASE + y_profile

    # 3. Post-Shock Evolution Time tau(y)
    # The shock hits each point of the corrugated interface at a slightly different time
    # After impact, Richtmyer impulsive growth formula applies:
    # amplitude growth da/dt = k * v_jump * A_t * a_0
    shock_dist = x_shock - x_interface_0
    has_impacted = shock_dist > 0.0
    tau = np.maximum(0.0, shock_dist / V_SHOCK)  # Local time elapsed since shock passage

    # 4. Nonlinear Mushroom Roll-Up Kinematics
    # Spikes (heavy fluid into light fluid, penetrating forward):
    # In RM instability, crests that extend forward get accelerated into mushroom heads.
    # Bubbles (light fluid into heavy fluid) flatten into rounded domes.
    # Growth factor grows linearly initially, then transitions to logarithmically/power-law saturated roll-up
    growth_scale = np.minimum(tau * 0.65, 2.8)

    # Asymmetry between spikes and bubbles (spikes are narrower and faster)
    spike_weight = np.where(y_profile > 0, 1.35, 0.75)
    dx_growth = growth_scale * y_profile * spike_weight

    # Vortex roll-up scroll displacement:
    # Baroclinic torque deposits vorticity proportional to d(y_profile)/dy
    # Roll-up spirals curl inward toward the spike centers
    dy_profile = np.zeros_like(Y_grid)
    for m in MODES:
        dy_profile += -m["amp"] * m["k"] * np.sin(m["k"] * Y_grid + m["phase"])

    vortex_strength = dy_profile * np.minimum(tau * 0.8, 2.2)

    # Secondary Kelvin-Helmholtz shear modulation along the trailing stems
    kh_freq = 11.0
    kh_shear = 0.08 * np.sin(kh_freq * (Y_grid + 0.4 * tau)) * np.exp(-np.abs(Y_grid) * 0.5) * np.minimum(tau * 0.5, 1.5)

    # Advected Interface Coordinates
    # Transmitted interface is carried forward by post-shock fluid velocity u_p
    post_shock_advection = 0.28 * tau
    x_int_deformed = x_interface_0 + post_shock_advection + dx_growth + kh_shear

    # Tangential curl displacement (mushroom scroll spiral formation)
    # Curl radius increases with tau
    curl_radius = 0.35 * np.sin(np.minimum(tau * 1.8, np.pi * 1.4))
    y_int_deformed = Y_grid + curl_radius * vortex_strength

    # 5. Density Field rho(X, Y)
    # Heavy gas is inside the corrugated cloud (x < x_int_deformed);
    # Light ambient gas is outside (x > x_int_deformed).
    # Signed distance approximation to the deformed interface
    dist_to_interface = X_grid - x_int_deformed

    # Smooth sigmoid transition of density across the contact discontinuity
    interface_width = 0.07 + 0.02 * np.sin(Y_grid * 3.0 + t)
    rho_interface = 1.0 / (1.0 + np.exp(dist_to_interface / interface_width))

    # Add intricate internal filamentary density layers (turbulent mixing cores)
    internal_layers = 0.25 * np.sin(7.0 * dist_to_interface + 3.0 * y_int_deformed) * rho_interface
    vortex_eyes = 0.40 * np.exp(-((dist_to_interface + 0.2)**2 + (y_int_deformed - 0.7)**2) / 0.12) + \
                  0.40 * np.exp(-((dist_to_interface + 0.2)**2 + (y_int_deformed + 0.7)**2) / 0.12) + \
                  0.30 * np.exp(-((dist_to_interface + 0.15)**2 + (y_int_deformed - 1.6)**2) / 0.10) + \
                  0.30 * np.exp(-((dist_to_interface + 0.15)**2 + (y_int_deformed + 1.6)**2) / 0.10)
    
    rho_total = np.clip(rho_interface + internal_layers + vortex_eyes * rho_interface, 0.0, 1.8)

    # 6. Compressible Shock and Acoustic Wavefield
    # Planar shock front with sharp steepening
    shock_front_width = 0.05
    shock_steep = np.exp(-((X_grid - x_shock) / shock_front_width)**2)

    # Shock Mach stem and diamond reflection patterns behind the shock
    mach_wave_k = 4.5
    mach_diamond_angle = 0.65
    mach_diamonds = 0.35 * np.cos(mach_wave_k * (X_grid - 0.5 * x_shock) + mach_diamond_angle * Y_grid * mach_wave_k) * \
                    0.35 * np.cos(mach_wave_k * (X_grid - 0.5 * x_shock) - mach_diamond_angle * Y_grid * mach_wave_k)
    mach_diamonds *= np.clip((x_shock - X_grid) / 2.0, 0.0, 1.0) * np.exp(-np.maximum(0.0, (x_shock - X_grid) - 2.5))

    # Acoustic rarefaction and cylindrical reverberation ripples originating from impact points
    acoustic_ripples = np.zeros_like(X_grid)
    for yi in [-1.4, -0.7, 0.0, 0.7, 1.4]:
        r_dist = np.sqrt((X_grid - X_INT_BASE)**2 + (Y_grid - yi)**2)
        phase_ac = 14.0 * r_dist - 8.0 * t
        acoustic_ripples += 0.08 * np.sin(phase_ac) * np.exp(-r_dist * 0.7) * (1.0 if t > 1.2 else 0.0)

    # 7. Surface Normal Calculation for 3D Chrome Shading
    # Compute spatial gradients of the combined optical density field
    combined_field = rho_total * 1.2 + shock_steep * 1.5 + mach_diamonds * 0.6 + acoustic_ripples * 0.4
    grad_y, grad_x = np.gradient(combined_field, dy, dx)

    # Construct normal map
    inv_norm = 1.0 / np.sqrt(grad_x**2 + grad_y**2 + 1.0)
    nx_map = -grad_x * inv_norm
    ny_map = -grad_y * inv_norm
    nz_map = inv_norm

    # 8. Specular Highlights (Blinn-Phong)
    ndoth1 = np.maximum(0.0, nx_map * h1[0] + ny_map * h1[1] + nz_map * h1[2])
    ndoth2 = np.maximum(0.0, nx_map * h2[0] + ny_map * h2[1] + nz_map * h2[2])
    specular1 = ndoth1**36.0
    specular2 = ndoth2**48.0

    # 9. Diffuse Illuminations
    diffuse1 = np.maximum(0.0, nx_map * light1[0] + ny_map * light1[1] + nz_map * light1[2])
    diffuse2 = np.maximum(0.0, nx_map * light2[0] + ny_map * light2[1] + nz_map * light2[2])

    return (
        rho_total,
        shock_steep,
        mach_diamonds,
        acoustic_ripples,
        diffuse1,
        diffuse2,
        specular1,
        specular2,
        x_shock,
        x_int_deformed,
        dy_profile,
        tau
    )


def render_field_to_buffer(
    rho_total,
    shock_steep,
    mach_diamonds,
    acoustic_ripples,
    diffuse1,
    diffuse2,
    specular1,
    specular2
):
    """
    Assembles the multi-tone curated color palette into the ARGB pixel buffer:
    - Background: Obsidian vacuum void (#05070f)
    - Dominant: Molten copper, warm amber, and incandescent sienna for heavy fluid scrolls
    - Secondary: Glacial azure and electric cyan for supersonic shock fronts and Mach diamonds
    - Accent: Triple-point spark glints and specular nodes in diamond-white and solar platinum
    """
    # Base background: Deep cosmic abyss
    r_field = np.full((Ny, Nx), 5.0, dtype=np.float32)
    g_field = np.full((Ny, Nx), 7.0, dtype=np.float32)
    b_field = np.full((Ny, Nx), 15.0, dtype=np.float32)

    # Ambient subtle interstellar dust gradation
    dist_center = np.sqrt(X_grid**2 + Y_grid**2)
    ambient_nebula = np.exp(-dist_center * 0.35) * 12.0
    r_field += ambient_nebula * 0.6
    g_field += ambient_nebula * 0.8
    b_field += ambient_nebula * 1.5

    # Heavy Gas Mushroom Scrolls (Molten Copper, Radiant Amber, Burnt Sienna)
    # Density modulation
    rho_norm = np.clip(rho_total / 1.4, 0.0, 1.0)
    copper_r = 230.0 * rho_norm + 45.0 * diffuse1
    copper_g = 115.0 * (rho_norm**1.4) + 30.0 * diffuse1
    copper_b = 35.0 * (rho_norm**2.2)

    r_field += copper_r * rho_norm
    g_field += copper_g * rho_norm
    b_field += copper_b * rho_norm

    # Acoustic Waves & Rarefaction Ripples (Deep Glacial Azure & Iris Violet)
    ac_pos = np.maximum(0.0, acoustic_ripples)
    r_field += ac_pos * 35.0
    g_field += ac_pos * 90.0
    b_field += ac_pos * 200.0

    # Mach Stem Diamonds & Supersonic Refraction Waves (Electric Cyan & Neon Teal)
    mach_pos = np.maximum(0.0, mach_diamonds)
    r_field += mach_pos * 40.0
    g_field += mach_pos * 180.0
    b_field += mach_pos * 235.0

    # Supersonic Planar Shock Front (Blinding Electric Cyan & Glacial White Ribbon)
    shock_glow = shock_steep * 220.0
    r_field += shock_glow * 0.75
    g_field += shock_glow * 0.95
    b_field += shock_glow * 1.10

    # Specular Glints and Fluid Chrome Reflections (Incandescent Diamond-White & Solar Platinum)
    spec_total = specular1 * 1.1 + specular2 * 0.9
    r_field += spec_total * 255.0
    g_field += spec_total * 245.0
    b_field += spec_total * 220.0

    # Final Clipping and Transfer to Buffer
    pixel_buffer[..., 1] = np.clip(r_field, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g_field, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b_field, 0, 255).astype(np.uint8)


def draw_frame():
    frame = py5.frame_count
    t = float(frame) / float(FPS)

    # 1. Compute Continuum Simulation State
    (
        rho_total,
        shock_steep,
        mach_diamonds,
        acoustic_ripples,
        diffuse1,
        diffuse2,
        specular1,
        specular2,
        x_shock,
        x_int_deformed,
        dy_profile,
        tau
    ) = compute_simulation_state(t, frame)

    # 2. Render Continuum Fields to High-Precision ARGB Pixel Buffer
    render_field_to_buffer(
        rho_total,
        shock_steep,
        mach_diamonds,
        acoustic_ripples,
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

    # 4. Lagrangian Particle Dynamics (Aerosol Soot, Ionization Sparks, Shock Filaments)
    # Coordinate mapping from simulation domain [-4, 4] x [-2.25, 2.25] to screen [width, height]
    def sim_to_screen(sx, sy):
        px = (sx - x_coords[0]) / (x_coords[-1] - x_coords[0]) * py5.width
        py = (y_coords[-1] - sy) / (y_coords[-1] - y_coords[0]) * py5.height
        return px, py

    # Spawn new particles dynamically based on shock interface interaction
    screen_shock_x = (x_shock - x_coords[0]) / (x_coords[-1] - x_coords[0]) * py5.width

    if len(particles) < MAX_PARTICLES and frame < TOTAL_FRAMES - 30:
        spawn_budget = min(40, MAX_PARTICLES - len(particles))
        for _ in range(spawn_budget):
            roll = random.random()

            if roll < 0.45:
                # Soot / Aerosol Tracer: along the rolling mushroom spiral lobes
                sample_y_idx = random.randint(10, Ny - 11)
                sim_y = float(y_coords[sample_y_idx])
                sim_x = float(x_int_deformed[sample_y_idx, Nx // 2]) + random.gauss(0.0, 0.18)
                px, py = sim_to_screen(sim_x, sim_y)

                # Fluid velocity from gradient and advection
                flow_vx = random.uniform(1.2, 3.8)
                flow_vy = -float(dy_profile[sample_y_idx, 0]) * random.uniform(1.5, 4.0)

                particles.append(AerosolParticle(
                    px, py,
                    ptype="soot",
                    vx=flow_vx,
                    vy=flow_vy,
                    life=random.uniform(50.0, 110.0),
                    radius=random.uniform(1.4, 2.8)
                ))

            elif roll < 0.78:
                # High-energy Shock Triple-Point Spark: spawned directly at the shock line
                if 0 <= screen_shock_x <= py5.width:
                    spark_y = random.uniform(50.0, py5.height - 50.0)
                    spark_angle = random.uniform(-np.pi * 0.4, np.pi * 0.4)
                    spark_speed = random.uniform(4.0, 9.5)
                    particles.append(AerosolParticle(
                        screen_shock_x + random.uniform(-5.0, 5.0),
                        spark_y,
                        ptype="spark",
                        vx=spark_speed * np.cos(spark_angle),
                        vy=spark_speed * np.sin(spark_angle),
                        life=random.uniform(25.0, 60.0),
                        radius=random.uniform(2.0, 4.5)
                    ))

            else:
                # Ionizing Filament Tracer: in the wake between vortices
                sample_y = random.uniform(-2.0, 2.0)
                sample_x = random.uniform(X_INT_BASE - 0.4, x_shock)
                px, py = sim_to_screen(sample_x, sample_y)
                particles.append(AerosolParticle(
                    px, py,
                    ptype="filament",
                    vx=random.uniform(0.5, 2.2),
                    vy=random.uniform(-1.0, 1.0),
                    life=random.uniform(40.0, 90.0),
                    radius=random.uniform(1.2, 2.2)
                ))

    # Update and Draw Lagrangian Particles with Additive Blending
    py5.blend_mode(py5.ADD)
    active_particles = []
    for p in particles:
        # Approximate local fluid flow
        p.update(flow_vx=random.uniform(0.5, 2.0), flow_vy=random.uniform(-0.5, 0.5))
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
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Active Particles: {len(particles)}")

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

"""
kinetic_icf_ablative_implosion_stagnation_2d
2D multi-physics kinetic simulation of Inertial Confinement Fusion (ICF):
laser/X-ray ablation drive, convergent spherical shock waves, ablative Rayleigh-Taylor
instability (RTI) spike-and-bubble growth with Bell-Plesset geometric convergence,
core stagnation rebound shock, thermonuclear ignition flash, and relativistic alpha-particle fireworks.

3840x2160 / 1920x1080 @ 60fps, 900 frames (15 seconds).
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
x_coords = np.linspace(-3.6, 3.6, Nx, dtype=np.float32)
y_coords = np.linspace(-2.025, 2.025, Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
dx = float(x_coords[1] - x_coords[0])
dy = float(y_coords[1] - y_coords[0])

# Precompute Polar Coordinates for Cylindrical/Spherical Symmetry
R_grid = np.sqrt(X_grid**2 + Y_grid**2)
Theta_grid = np.arctan2(Y_grid, X_grid)

# Dual Specular Light Vectors for Plasma Chrome Normal Shading
light1 = np.array([0.58, -0.62, 0.53], dtype=np.float32)
light1 /= np.linalg.norm(light1)
light2 = np.array([-0.52, 0.58, 0.63], dtype=np.float32)
light2 /= np.linalg.norm(light2)
view_vec = np.array([0.0, 0.0, 1.0], dtype=np.float32)
h1 = (light1 + view_vec) / np.linalg.norm(light1 + view_vec)
h2 = (light2 + view_vec) / np.linalg.norm(light2 + view_vec)

# ARGB pixel buffer for py5 (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Physical Parameters & RTI Modes
R0 = 2.45                    # Initial outer capsule radius
R_MIN = 0.32                 # Minimum stagnation core radius
T_STAG = 9.0                 # Core stagnation epoch (seconds)
RTI_MODES = [4, 6, 8, 10, 12]
RTI_AMPS = [0.12, 0.16, 0.14, 0.09, 0.05]
RTI_PHASES = [0.2, 1.1, 2.3, 0.7, 1.9]


class Particle:
    """Lagrangian tracer particle for fuel spikes, coronal blowoff, or thermonuclear alpha sparks."""
    def __init__(self, x, y, ptype="spike", vx=0.0, vy=0.0, life=120.0, radius=2.5, color_rgba=None):
        self.x = float(x)
        self.y = float(y)
        self.ptype = ptype
        self.vx = float(vx)
        self.vy = float(vy)
        self.life = float(life)
        self.max_life = float(life)
        self.radius = float(radius)
        self.color_rgba = color_rgba or (255, 255, 255, 200)
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

        # Kinematic evolution based on particle species
        if self.ptype == "spike":
            # Dense cryogenic fuel bead plunging into inward spike
            self.vx *= 0.985
            self.vy *= 0.985
            self.x += self.vx
            self.y += self.vy
        elif self.ptype == "corona":
            # Outward expanding ablation blowoff ion
            self.vx *= 1.008
            self.vy *= 1.008
            self.x += self.vx
            self.y += self.vy
        elif self.ptype == "alpha":
            # Relativistic thermonuclear alpha/neutron spark
            self.vx *= 0.975
            self.vy *= 0.975
            self.x += self.vx
            self.y += self.vy


# Particle System
particles = []


def seed_initial_particles():
    """Seed initial cryogenic fuel tracers along the capsule perimeter."""
    for _ in range(1200):
        angle = random.uniform(-np.pi, np.pi)
        r = R0 * random.uniform(0.92, 1.04)
        vx = -0.0035 * np.cos(angle) + random.uniform(-0.001, 0.001)
        vy = -0.0035 * np.sin(angle) + random.uniform(-0.001, 0.001)
        particles.append(
            Particle(
                r * np.cos(angle),
                r * np.sin(angle),
                ptype="spike",
                vx=vx,
                vy=vy,
                life=random.uniform(500, 900),
                radius=random.uniform(2.0, 3.8),
                color_rgba=(0, 240, 255, 210)
            )
        )


def compute_icf_state(t, frame):
    """
    Vectorized computation of continuous physical ICF fields:
    1. Implosion base radius R_base(t)
    2. Ablative RTI mode superposition & non-linear spike sharpening
    3. Cryogenic compressed fuel shell density
    4. Thermonuclear hot spot core temperature & Bremsstrahlung flash
    5. Rebound shock wave propagation
    6. Coronal X-ray ablation blowoff
    7. Blinn-Phong surface normal & specular highlights
    """
    # 1. Base Implosion Trajectory
    if t <= T_STAG:
        # Inward acceleration phase
        tau = t / T_STAG
        r_base = R0 - (R0 - R_MIN) * (tau**1.75)
        implosion_vel = -1.75 * (R0 - R_MIN) * (tau**0.75) / T_STAG
    else:
        # Post-stagnation rebound and burn expansion phase
        tau_post = (t - T_STAG) / (DURATION_SEC - T_STAG)
        r_base = R_MIN + 0.85 * (1.0 - np.exp(-3.2 * tau_post))
        implosion_vel = 0.85 * 3.2 * np.exp(-3.2 * tau_post) / (DURATION_SEC - T_STAG)

    # 2. Multi-Mode Ablative RTI Perturbation with Bell-Plesset Convergence
    delta_r = np.zeros_like(Theta_grid)
    growth_factor = min(1.0, (t / 7.5)**2.2) * ((R0 / max(0.1, r_base))**1.15)

    for mode, amp, phase in zip(RTI_MODES, RTI_AMPS, RTI_PHASES):
        phase_drift = phase + 0.15 * np.sin(t * 0.8 + mode)
        delta_r += amp * np.cos(mode * Theta_grid + phase_drift)

    # Non-linear Layzer spike sharpening: inward cusps are narrow and deep, outward bubbles are broad
    delta_r_nl = delta_r - 0.38 * (delta_r**2)
    r_shell_pert = np.maximum(0.08, r_base + delta_r_nl * growth_factor * 0.42)

    # 3. Cryogenic Compressed Fuel Shell Density rho_fuel(r, theta, t)
    # Shell thickness compresses as sqrt(r_base / R0)
    sigma_shell = 0.16 * np.sqrt(max(0.12, r_base) / R0)
    compression_ratio = (R0 / max(0.2, r_base))**1.35
    rho_fuel = np.exp(-((R_grid - r_shell_pert)**2) / (2.0 * sigma_shell**2)) * compression_ratio

    # 4. Thermonuclear Hot Spot Core Temperature & Bremsstrahlung Flash
    flash_envelope = np.exp(-((t - T_STAG) / 0.55)**2)
    burn_sustain = 0.45 * (1.0 / (1.0 + np.exp(-(t - T_STAG - 0.3) * 3.0)))
    core_intensity = 1.0 + 4.8 * flash_envelope + 2.2 * burn_sustain

    core_radius = max(0.12, r_base * 0.72)
    t_core = (core_intensity / (1.0 + (R_grid / core_radius)**4.0)) * (R_grid <= (r_shell_pert + 0.1))

    # 5. Convergent / Rebound Bremsstrahlung Shock Waves
    shock_field = np.zeros_like(R_grid)
    if t < T_STAG:
        # Inward converging precursor shock
        r_lead_shock = max(0.05, r_base * 0.6)
        shock_field = np.exp(-((R_grid - r_lead_shock)**2) / 0.04) * (0.8 + 0.4 * np.sin(20.0 * R_grid))
    else:
        # Outward explosive rebound shock
        t_reb = t - T_STAG
        r_reb_shock = 0.25 + 0.92 * t_reb
        shock_env = np.exp(-((R_grid - r_reb_shock)**2) / (0.06 + 0.04 * t_reb))
        shock_waves = np.sin(24.0 * (R_grid - r_reb_shock) - t_reb * 12.0)
        shock_field = shock_env * (1.2 + 0.8 * shock_waves) / (1.0 + 0.45 * R_grid)

    # 6. Coronal X-Ray Ablation Blowoff (Expanding Outward)
    corona_mask = (R_grid > (r_shell_pert - 0.05))
    r_dist = np.maximum(0.0, R_grid - r_shell_pert)
    corona_blowoff = np.exp(-r_dist / 0.75) * (1.0 + 0.25 * np.cos(6.0 * Theta_grid - t * 2.5)) * corona_mask
    corona_blowoff *= min(1.0, t / 1.8)

    # 7. Total Optical Relief Map for 3D Specular Shading
    relief_field = (
        rho_fuel * 1.7 +
        t_core * 2.4 +
        shock_field * 0.85 +
        corona_blowoff * 0.45
    )

    # 8. Surface Normal Gradient Field
    grad_y, grad_x = np.gradient(relief_field, dy, dx)
    inv_norm = 1.0 / np.sqrt(grad_x**2 + grad_y**2 + 1.0)
    nx_map = -grad_x * inv_norm
    ny_map = -grad_y * inv_norm
    nz_map = inv_norm

    # 9. Dual Specular Glints (Blinn-Phong)
    ndoth1 = np.maximum(0.0, nx_map * h1[0] + ny_map * h1[1] + nz_map * h1[2])
    ndoth2 = np.maximum(0.0, nx_map * h2[0] + ny_map * h2[1] + nz_map * h2[2])
    specular1 = ndoth1**42.0
    specular2 = ndoth2**56.0

    # 10. Diffuse Lighting
    diffuse1 = np.maximum(0.0, nx_map * light1[0] + ny_map * light1[1] + nz_map * light1[2])
    diffuse2 = np.maximum(0.0, nx_map * light2[0] + ny_map * light2[1] + nz_map * light2[2])

    return (
        r_base,
        r_shell_pert,
        rho_fuel,
        t_core,
        shock_field,
        corona_blowoff,
        flash_envelope,
        diffuse1,
        diffuse2,
        specular1,
        specular2
    )


def render_field_to_buffer(
    rho_fuel,
    t_core,
    shock_field,
    corona_blowoff,
    flash_envelope,
    diffuse1,
    diffuse2,
    specular1,
    specular2
):
    """
    Composes color fields into the ARGB pixel buffer using the curated 4-color palette:
    1. Thermonuclear Stagnation Core & Flash: Diamond-White (#ffffff) & Incandescent Gold (#ffb703)
    2. Cryogenic Compressed Fuel Shell & RTI Spikes: Glacial Electric Cyan (#00f0ff) & Sapphire Blue (#0077b6)
    3. Coronal Ablation Blowoff: Radiant Cerise Magenta (#b5179e) & Ionized Violet (#7209b7)
    4. Vacuum / Hohlraum Void: Deep Obsidian Indigo (#02040b, #080d1e)
    """
    # Background: Radial cosmic vacuum abyss
    r_norm = np.clip(R_grid / 3.8, 0.0, 1.0)
    r_field = 2.0 + 8.0 * r_norm
    g_field = 4.0 + 10.0 * r_norm
    b_field = 11.0 + 26.0 * r_norm

    # 1. Coronal Ablation Blowoff (Radiant Cerise & Violet)
    corona_norm = np.clip(corona_blowoff * 1.4, 0.0, 1.8)
    r_field += corona_norm * 175.0
    g_field += corona_norm * 24.0
    b_field += corona_norm * 165.0

    # 2. Cryogenic DT Fuel Shell & RTI Spikes (Electric Cyan & Sapphire)
    fuel_norm = np.clip(rho_fuel * 0.95, 0.0, 2.2)
    r_field += fuel_norm * 0.0
    g_field += fuel_norm * 225.0
    b_field += fuel_norm * 255.0

    # Add diffuse lighting relief on fuel shell
    diff_total = diffuse1 * 0.65 + diffuse2 * 0.45
    r_field += fuel_norm * diff_total * 40.0
    g_field += fuel_norm * diff_total * 95.0
    b_field += fuel_norm * diff_total * 130.0

    # 3. Concentric Rebound Bremsstrahlung Shock Waves (Phosphor Mint & Glacial Azure)
    shock_norm = np.clip(shock_field * 1.2, 0.0, 2.0)
    r_field += shock_norm * 110.0
    g_field += shock_norm * 235.0
    b_field += shock_norm * 255.0

    # 4. Thermonuclear Hot Spot Core & Ignition Flash (Solar Gold to Diamond White)
    core_norm = np.clip(t_core * 0.85, 0.0, 3.5)
    r_field += core_norm * 255.0
    g_field += core_norm * 215.0
    b_field += core_norm * 120.0

    # Extra intense flash saturation at ignition peak
    flash_boost = flash_envelope * 110.0
    r_field += flash_boost
    g_field += flash_boost * 0.95
    b_field += flash_boost * 0.85

    # 5. Dual Blinn-Phong Specular Plasma Chrome Glints
    spec_total = specular1 * 1.35 + specular2 * 1.05
    r_field += spec_total * 255.0
    g_field += spec_total * 250.0
    b_field += spec_total * 240.0

    # Final Clipping and Transfer to Buffer
    pixel_buffer[..., 1] = np.clip(r_field, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g_field, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b_field, 0, 255).astype(np.uint8)


def update_and_draw_particles(t, r_base, r_shell_pert, flash_envelope):
    """Update and render the 3 classes of Lagrangian particles with additive blending."""
    global particles

    # Spawn new coronal blowoff ions
    if t < 14.5 and len(particles) < 2800:
        for _ in range(8):
            angle = random.uniform(-np.pi, np.pi)
            r = r_base * random.uniform(1.05, 1.25)
            speed = random.uniform(0.006, 0.016)
            vx = speed * np.cos(angle) + random.uniform(-0.002, 0.002)
            vy = speed * np.sin(angle) + random.uniform(-0.002, 0.002)
            particles.append(
                Particle(
                    r * np.cos(angle),
                    r * np.sin(angle),
                    ptype="corona",
                    vx=vx,
                    vy=vy,
                    life=random.uniform(40, 90),
                    radius=random.uniform(1.8, 3.2),
                    color_rgba=(220, 30, 180, 180)
                )
            )

    # Spawn thermonuclear alpha/neutron spark burst at stagnation flash
    if 8.9 <= t <= 9.3:
        num_sparks = int(80 * (1.0 + 3.0 * flash_envelope))
        for _ in range(num_sparks):
            angle = random.uniform(-np.pi, np.pi)
            speed = random.uniform(0.018, 0.045)
            vx = speed * np.cos(angle)
            vy = speed * np.sin(angle)
            particles.append(
                Particle(
                    random.uniform(-0.05, 0.05),
                    random.uniform(-0.05, 0.05),
                    ptype="alpha",
                    vx=vx,
                    vy=vy,
                    life=random.uniform(30, 80),
                    radius=random.uniform(2.5, 5.0),
                    color_rgba=(255, 240, 180, 240)
                )
            )

    # Transform coordinates from simulation domain [-3.6, 3.6]x[-2.025, 2.025] to screen pixels
    scale_x = float(py5.width) / 7.2
    scale_y = float(py5.height) / 4.05
    cx = float(py5.width) * 0.5
    cy = float(py5.height) * 0.5

    py5.blend_mode(py5.ADD)
    py5.no_stroke()

    alive_particles = []
    for p in particles:
        p.update()
        if p.is_dead:
            continue
        alive_particles.append(p)

        # Screen coordinates
        sx = cx + p.x * scale_x
        sy = cy - p.y * scale_y  # Invert Y for screen display

        if not (-50 <= sx <= py5.width + 50 and -50 <= sy <= py5.height + 50):
            continue

        life_ratio = p.life / p.max_life
        r, g, b, base_alpha = p.color_rgba
        alpha = base_alpha * life_ratio

        # Draw particle trail
        if len(p.history) >= 2:
            py5.stroke(r, g, b, alpha * 0.6)
            py5.stroke_weight(p.radius * 0.6)
            for i in range(len(p.history) - 1):
                x1, y1 = p.history[i]
                x2, y2 = p.history[i + 1]
                py5.line(cx + x1 * scale_x, cy - y1 * scale_y, cx + x2 * scale_x, cy - y2 * scale_y)
            py5.no_stroke()

        # Draw glowing particle core
        py5.fill(r, g, b, alpha)
        py5.circle(sx, sy, p.radius * (1.0 + (1.0 - life_ratio) * 0.5))

        # Soft outer aura
        py5.fill(r, g, b, alpha * 0.25)
        py5.circle(sx, sy, p.radius * 2.8)

    particles = alive_particles
    py5.blend_mode(py5.BLEND)


def draw_frame():
    frame = py5.frame_count
    t = float(frame) / float(FPS)

    # 1. Compute Continuum ICF State
    (
        r_base,
        r_shell_pert,
        rho_fuel,
        t_core,
        shock_field,
        corona_blowoff,
        flash_envelope,
        diffuse1,
        diffuse2,
        specular1,
        specular2
    ) = compute_icf_state(t, frame)

    # 2. Render Continuum Fields to High-Precision ARGB Pixel Buffer
    render_field_to_buffer(
        rho_fuel,
        t_core,
        shock_field,
        corona_blowoff,
        flash_envelope,
        diffuse1,
        diffuse2,
        specular1,
        specular2
    )

    # 3. Blit Buffer to Canvas
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
        packed = (a << 24) | (r << 16) | (g << 8) | b
        img.pixels[:] = packed.flatten()
        img.update_pixels()

    py5.image(img, 0, 0, py5.width, py5.height)

    # 4. Render Lagrangian Particles & Filament Kinematics
    update_and_draw_particles(t, r_base, r_shell_pert, flash_envelope)

    # 5. Save Current Frame to Temporary Disk Cache
    frame_path = FRAMES_DIR / f"frame-{frame:04d}.png"
    py5.save_frame(str(frame_path))

    # Save preview image at peak stagnation flash epoch (frame 550, t ~ 9.17s)
    if frame == 550:
        preview_path = SKETCH_DIR / PREVIEW_FILENAME
        py5.save_frame(str(preview_path))
        print(f"[Preview Saved] Stagnation peak preview captured: {preview_path}")

    # Safety check on first frame
    if frame == 1:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {frame} (std < 1.0). Aborting.")
            os._exit(1)

    # Progress feedback
    if frame % 60 == 0:
        progress_pct = (frame / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Particles: {len(particles)}")

    # 6. Video Compilation & Cleanup when Total Frames Reached
    if frame >= TOTAL_FRAMES:
        py5.exit_sketch()

        print("\n[Render Complete] Compiling H.264 video with FFmpeg...")
        output_mp4 = SKETCH_DIR / "output.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-preset", "medium",
            str(output_mp4)
        ]

        try:
            subprocess.run(cmd, check=True)
            print(f"[Video Compiled] Master MP4 saved: {output_mp4}")
        except subprocess.CalledProcessError as e:
            print(f"[FFmpeg Error] Failed to encode video: {e}")
            sys.exit(1)

        # Fallback preview if frame 550 didn't trigger
        preview_path = SKETCH_DIR / PREVIEW_FILENAME
        if not preview_path.exists():
            midpoint_frame = FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png"
            if midpoint_frame.exists():
                shutil.copyfile(midpoint_frame, preview_path)
                print(f"[Preview Saved] Fallback preview image saved: {preview_path}")

        # Clean up temporary frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.\n")

        os._exit(0)


def settings():
    py5.size(SIZE[0], SIZE[1], py5.P2D)


def setup():
    py5.frame_rate(FPS)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    seed_initial_particles()
    print(f"[Setup Complete] Rendering {WORK_NAME} ({SIZE[0]}x{SIZE[1]} @ {FPS}fps, {TOTAL_FRAMES} frames)...")


def draw():
    try:
        draw_frame()
    except Exception:
        import traceback
        traceback.print_exc()
        os._exit(1)


if __name__ == "__main__":
    py5.run_sketch()

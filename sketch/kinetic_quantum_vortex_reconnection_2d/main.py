"""
kinetic_quantum_vortex_reconnection_2d
Quantum fluid dynamics simulation of topological vortex reconnection in a Bose-Einstein Condensate:
Gross-Pitaevskii macroscopic wavefunction phase winding, universal square-root reconnection scaling,
orthogonal cusp recoil, acoustic phonon sound burst emission, and Lagrangian Bohmian tracer kinematics.

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

# Dual Specular Light Vectors for Quantum Superfluid Chrome Shading
light1 = np.array([0.55, -0.60, 0.58], dtype=np.float32)
light1 /= np.linalg.norm(light1)
light2 = np.array([-0.50, 0.55, 0.67], dtype=np.float32)
light2 /= np.linalg.norm(light2)
view_vec = np.array([0.0, 0.0, 1.0], dtype=np.float32)
h1 = (light1 + view_vec) / np.linalg.norm(light1 + view_vec)
h2 = (light2 + view_vec) / np.linalg.norm(light2 + view_vec)

# ARGB pixel buffer for py5 (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Physical Parameters of the Bose-Einstein Condensate
HEALING_LENGTH = 0.16   # Vortex core radius xi
SOUND_SPEED = 1.6       # Superfluid phonon velocity c_s


class SuperfluidParticle:
    """Lagrangian tracer: Bohmian superfluid flow tracer or acoustic reconnection spark."""
    def __init__(self, x, y, ptype="bohmian", vx=0.0, vy=0.0, life=60.0, radius=2.0):
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

        if self.ptype == "bohmian":
            # Circulating in the quantized superfluid velocity field
            self.x += self.vx
            self.y += self.vy
        elif self.ptype == "reconn_spark":
            # Explosive radial expulsion from the reconnection cusp
            self.vx *= 0.93
            self.vy *= 0.93
            self.x += self.vx
            self.y += self.vy
        elif self.ptype == "phonon":
            # Acoustic shockwave packet
            self.x += self.vx
            self.y += self.vy
            self.radius += 0.04

    def draw(self, w, h):
        alpha_frac = max(0.0, min(1.0, self.life / self.max_life))
        pulse = 0.7 + 0.3 * np.sin(self.life * 0.28)

        if self.ptype == "bohmian":
            # Phosphor emerald / mint Bohmian tracer
            col_a = int(alpha_frac * 210 * pulse)
            py5.stroke(25, 240, 165, col_a)
            py5.stroke_weight(self.radius * (0.8 + 0.4 * alpha_frac))
            py5.point(self.x, self.y)

            if len(self.history) > 1:
                py5.stroke(0, 180, 210, int(col_a * 0.45))
                py5.stroke_weight(max(1.0, self.radius * 0.5))
                hx, hy = self.history[-2]
                py5.line(hx, hy, self.x, self.y)

        elif self.ptype == "reconn_spark":
            # Incandescent diamond-white / solar gold detonation spark
            col_a = int(alpha_frac * 255)
            glow_r = self.radius * (1.6 + (1.0 - alpha_frac) * 2.0)
            py5.no_stroke()
            py5.fill(255, 255, 255, col_a)
            py5.ellipse(self.x, self.y, glow_r * 0.8, glow_r * 0.8)
            py5.fill(255, 210, 80, int(col_a * 0.7))
            py5.ellipse(self.x, self.y, glow_r * 1.8, glow_r * 1.8)

        elif self.ptype == "phonon":
            # Electric cyan acoustic wavefront ripple
            col_a = int(alpha_frac * 170)
            py5.no_fill()
            py5.stroke(70, 220, 255, col_a)
            py5.stroke_weight(self.radius * 0.6)
            py5.ellipse(self.x, self.y, self.radius * 3.5, self.radius * 3.5)


particles = []
MAX_PARTICLES = 1400


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    py5.background(3, 7, 18)


def compute_quantum_vortex_state(t, frame_idx):
    """
    Computes the 2D Gross-Pitaevskii superfluid state during topological vortex reconnection:
    - Vortex positions governed by delta(t) ~ sqrt(|t - t_0|) scaling
    - Pre-reconnection approach and post-reconnection orthogonal recoil
    - Superfluid phase winding theta(x, y, t) with 2*pi branch cuts
    - Condensate density depression cores rho(x, y, t)
    - Acoustic phonon shock rings emitted upon reconnection
    """
    # Periodic reconnection cycle
    cycle_period = 3.6
    t_reconn = 1.8
    dt = (t % cycle_period) - t_reconn

    # Reconnection scaling parameter A
    scale_a = 1.35
    sqrt_dt = scale_a * np.sqrt(max(0.008, np.abs(dt)))

    # Vortex Positions: 4 vortices interacting symmetrically
    # Before reconnection (dt < 0):
    # Vortices are paired vertically (x = +/- d_x, y = +/- d_y), moving horizontally toward center
    # After reconnection (dt >= 0):
    # Topology has exchanged! Vortices are now paired horizontally, recoiling vertically away!
    if dt < 0:
        # Approaching horizontally
        vx1, vy1 = -sqrt_dt, 0.75 + 0.3 * np.abs(dt)    # Top-left (+1)
        vx2, vy2 = -sqrt_dt, -0.75 - 0.3 * np.abs(dt)   # Bottom-left (-1)
        vx3, vy3 = sqrt_dt, 0.75 + 0.3 * np.abs(dt)     # Top-right (-1)
        vx4, vy4 = sqrt_dt, -0.75 - 0.3 * np.abs(dt)    # Bottom-right (+1)
        reconn_flash = 0.0
    else:
        # Recoiling vertically after topological exchange
        vx1, vy1 = -0.75 - 0.3 * dt, sqrt_dt            # Left-top (+1)
        vx2, vy2 = 0.75 + 0.3 * dt, sqrt_dt             # Right-top (-1)
        vx3, vy3 = -0.75 - 0.3 * dt, -sqrt_dt           # Left-bottom (-1)
        vx4, vy4 = 0.75 + 0.3 * dt, -sqrt_dt            # Right-bottom (+1)
        # Detonation flash decaying exponentially
        reconn_flash = float(np.exp(-dt * 3.5))

    vortices = [
        (vx1, vy1, 1.0),
        (vx2, vy2, -1.0),
        (vx3, vy3, -1.0),
        (vx4, vy4, 1.0)
    ]

    # 1. Superfluid Phase Winding theta(X, Y)
    phase_field = np.zeros_like(X_grid)
    density_field = np.ones_like(X_grid)

    for vx, vy, charge in vortices:
        dx_v = X_grid - vx
        dy_v = Y_grid - vy
        r_v = np.sqrt(dx_v**2 + dy_v**2)

        # Phase accumulation
        theta_v = np.arctan2(dy_v, dx_v)
        phase_field += charge * theta_v

        # Condensate core density depletion ~ tanh^2(r / xi)
        density_field *= np.tanh(r_v / HEALING_LENGTH)**2

    # 2. Reconnection Acoustic Phonon Shock Burst
    acoustic_burst = np.zeros_like(X_grid)
    if dt >= 0:
        r_center = np.sqrt(X_grid**2 + Y_grid**2)
        wave_front = SOUND_SPEED * dt
        wave_arg = 18.0 * (r_center - wave_front)
        # Concentric acoustic shock ripples spreading outward
        acoustic_burst = reconn_flash * 1.8 * np.cos(wave_arg) * np.exp(-((r_center - wave_front) / 0.45)**2)

    # 3. Microscopic Quantum Interference Fringes
    # Superfluid phase contours create macroscopic density fringes cos(4*theta)
    phase_fringes = 0.35 * np.cos(4.0 * phase_field) * np.sqrt(density_field)

    # 4. Total Quantum Superfluid Relief Field
    relief_field = (
        np.sqrt(density_field) * 1.4 +
        phase_fringes * 0.6 +
        acoustic_burst * 0.9
    )

    # 5. Surface Normal Calculation for 3D Specular Shading
    grad_y, grad_x = np.gradient(relief_field, dy, dx)
    inv_norm = 1.0 / np.sqrt(grad_x**2 + grad_y**2 + 1.0)
    nx_map = -grad_x * inv_norm
    ny_map = -grad_y * inv_norm
    nz_map = inv_norm

    # 6. Specular Highlights (Blinn-Phong)
    ndoth1 = np.maximum(0.0, nx_map * h1[0] + ny_map * h1[1] + nz_map * h1[2])
    ndoth2 = np.maximum(0.0, nx_map * h2[0] + ny_map * h2[1] + nz_map * h2[2])
    specular1 = ndoth1**38.0
    specular2 = ndoth2**52.0

    # 7. Diffuse Illuminations
    diffuse1 = np.maximum(0.0, nx_map * light1[0] + ny_map * light1[1] + nz_map * light1[2])
    diffuse2 = np.maximum(0.0, nx_map * light2[0] + ny_map * light2[1] + nz_map * light2[2])

    return (
        density_field,
        phase_field,
        phase_fringes,
        acoustic_burst,
        reconn_flash,
        diffuse1,
        diffuse2,
        specular1,
        specular2,
        vortices,
        dt
    )


def render_field_to_buffer(
    density_field,
    phase_field,
    phase_fringes,
    acoustic_burst,
    reconn_flash,
    diffuse1,
    diffuse2,
    specular1,
    specular2
):
    """
    Composes the cryogenic superfluid color palette into the ARGB pixel buffer:
    - Background: Cryogenic sub-Kelvin vacuum abyss (#030712) and sapphire navy (#0b152d)
    - Dominant: Superfluid density and phase winding ripples in radiant emerald mint (#10f0a0), phosphor turquoise (#00d2c4)
    - Secondary: Vortex core halos and acoustic dispersion fringes in actinic ultraviolet (#8030ff) and electric cyan (#32a0ff)
    - Accent: Reconnection cusp detonation flash and sound nodes in diamond-white (#ffffff) and solar platinum (#fff0c0)
    """
    # Base background: Deep cryogenic vacuum void
    r_field = np.full((Ny, Nx), 3.0, dtype=np.float32)
    g_field = np.full((Ny, Nx), 7.0, dtype=np.float32)
    b_field = np.full((Ny, Nx), 18.0, dtype=np.float32)

    # Ambient condensate bulk (Deep Sapphire Navy & Glacial Azure)
    rho_sqrt = np.sqrt(density_field)
    bulk_r = rho_sqrt * (12.0 + 25.0 * diffuse1)
    bulk_g = rho_sqrt * (28.0 + 55.0 * diffuse1)
    bulk_b = rho_sqrt * (70.0 + 90.0 * diffuse1)
    r_field += bulk_r
    g_field += bulk_g
    b_field += bulk_b

    # Phase Winding Contours (Radiant Emerald Mint & Phosphor Turquoise)
    fringe_norm = np.maximum(0.0, phase_fringes)
    mint_r = fringe_norm * 16.0
    mint_g = fringe_norm * 240.0
    mint_b = fringe_norm * 160.0
    r_field += mint_r
    g_field += mint_g
    b_field += mint_b

    # Actinic Ultraviolet Halos around Zero-Density Cores
    core_halo = (1.0 - density_field) * 160.0
    r_field += core_halo * 0.5
    g_field += core_halo * 0.15
    b_field += core_halo * 1.0

    # Acoustic Phonon Shock Burst (Electric Glacial Cyan & Ice White Waves)
    ac_pos = np.maximum(0.0, acoustic_burst)
    r_field += ac_pos * 90.0
    g_field += ac_pos * 225.0
    b_field += ac_pos * 255.0

    # Reconnection Cusp Central Detonation Core
    if reconn_flash > 0.02:
        dist_c = np.sqrt(X_grid**2 + Y_grid**2)
        flash_core = reconn_flash * np.exp(-(dist_c / 0.28)**2) * 255.0
        r_field += flash_core
        g_field += flash_core * 0.96
        b_field += flash_core * 0.85

    # Specular Quantum Chrome Reflections (Incandescent Diamond-White & Platinum)
    spec_total = specular1 * 1.15 + specular2 * 0.95
    r_field += spec_total * 255.0
    g_field += spec_total * 250.0
    b_field += spec_total * 235.0

    # Final Clipping and Transfer to Buffer
    pixel_buffer[..., 1] = np.clip(r_field, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g_field, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b_field, 0, 255).astype(np.uint8)


def draw_frame():
    frame = py5.frame_count
    t = float(frame) / float(FPS)

    # 1. Compute Continuum Superfluid State
    (
        density_field,
        phase_field,
        phase_fringes,
        acoustic_burst,
        reconn_flash,
        diffuse1,
        diffuse2,
        specular1,
        specular2,
        vortices,
        dt
    ) = compute_quantum_vortex_state(t, frame)

    # 2. Render Continuum Fields to High-Precision ARGB Pixel Buffer
    render_field_to_buffer(
        density_field,
        phase_field,
        phase_fringes,
        acoustic_burst,
        reconn_flash,
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

    # 4. Lagrangian Particle Dynamics (Bohmian Streamlines, Reconnection Detonation Sparks)
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
                # Bohmian tracer circulating around a randomly chosen vortex
                vx_c, vy_c, q = random.choice(vortices)
                r_orbit = random.uniform(HEALING_LENGTH * 1.2, 0.85)
                ang = random.uniform(-np.pi, np.pi)
                sim_x = vx_c + r_orbit * np.cos(ang)
                sim_y = vy_c + r_orbit * np.sin(ang)
                px, py = sim_to_screen(sim_x, sim_y)

                # Tangential quantized velocity v = q / r
                v_mag = random.uniform(2.5, 6.0)
                particles.append(SuperfluidParticle(
                    px, py,
                    ptype="bohmian",
                    vx=-q * v_mag * np.sin(ang),
                    vy=q * v_mag * np.cos(ang),
                    life=random.uniform(40.0, 90.0),
                    radius=random.uniform(1.4, 2.6)
                ))

            elif roll < 0.75:
                # Acoustic phonon wavefront ripple
                if dt >= 0 and dt < 1.2:
                    r_ph = SOUND_SPEED * dt + random.gauss(0.0, 0.1)
                    ang_ph = random.uniform(-np.pi, np.pi)
                    px, py = sim_to_screen(r_ph * np.cos(ang_ph), r_ph * np.sin(ang_ph))
                    particles.append(SuperfluidParticle(
                        px, py,
                        ptype="phonon",
                        vx=SOUND_SPEED * 2.5 * np.cos(ang_ph),
                        vy=SOUND_SPEED * 2.5 * np.sin(ang_ph),
                        life=random.uniform(30.0, 65.0),
                        radius=random.uniform(1.2, 2.2)
                    ))

            else:
                # Reconnection cusp detonation spark burst at center
                if reconn_flash > 0.15:
                    sim_x = random.gauss(0.0, 0.15)
                    sim_y = random.gauss(0.0, 0.15)
                    px, py = sim_to_screen(sim_x, sim_y)
                    spark_speed = random.uniform(5.5, 12.0)
                    spark_ang = random.uniform(-np.pi, np.pi)
                    particles.append(SuperfluidParticle(
                        px, py,
                        ptype="reconn_spark",
                        vx=spark_speed * np.cos(spark_ang),
                        vy=spark_speed * np.sin(spark_ang),
                        life=random.uniform(20.0, 50.0),
                        radius=random.uniform(2.0, 4.5)
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
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Reconn Flash: {reconn_flash:.2f} | Particles: {len(particles)}")

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

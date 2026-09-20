"""
kinetic_josephson_vortex_swihart_solitons_2d
Quantum superconductivity simulation of relativistic Josephson vortices (fluxons)
in a Long Josephson Junction (LJJ): Swihart velocity propagation, Lorentz contraction,
Cherenkov plasma wave shedding, fluxon-antifluxon topological annihilation bursts,
and Meissner supercurrent loop kinematics.

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

# Dual Specular Light Vectors for Superconducting Niobium Chrome Shading
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

# Physical Parameters of the Long Josephson Junction
BARRIER_HALF_HEIGHT = 0.38   # Insulating tunnel oxide layer thickness
SWIHART_VELOCITY = 1.0       # Normalized Swihart velocity c_bar = 1.0
LAMBDA_J = 0.42              # Josephson penetration depth


class CooperParticle:
    """Lagrangian particle representing supercurrent carriers, annihilation sparks, or Cherenkov quanta."""
    def __init__(self, x, y, ptype="supercurrent", vx=0.0, vy=0.0, life=60.0, radius=2.0):
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

        if self.ptype == "supercurrent":
            # Meissner screening vortex orbit around fluxon
            self.x += self.vx
            self.y += self.vy
        elif self.ptype == "annihilation_spark":
            # High-velocity explosive burst from topological collision
            self.vx *= 0.94
            self.vy *= 0.94
            self.x += self.vx
            self.y += self.vy
        elif self.ptype == "cherenkov":
            # Wavepacket tracer in the plasma wake
            self.x += self.vx
            self.y += self.vy

    def draw(self, w, h):
        alpha_frac = max(0.0, min(1.0, self.life / self.max_life))
        pulse = 0.7 + 0.3 * np.sin(self.life * 0.3)

        if self.ptype == "supercurrent":
            # Luminous amber / golden supercurrent streamline tracer
            col_a = int(alpha_frac * 210 * pulse)
            py5.stroke(255, 185, 50, col_a)
            py5.stroke_weight(self.radius * (0.8 + 0.4 * alpha_frac))
            py5.point(self.x, self.y)

            if len(self.history) > 1:
                py5.stroke(235, 120, 30, int(col_a * 0.5))
                py5.stroke_weight(max(1.0, self.radius * 0.6))
                hx, hy = self.history[-2]
                py5.line(hx, hy, self.x, self.y)

        elif self.ptype == "annihilation_spark":
            # Incandescent diamond-white / solar platinum collision spark
            col_a = int(alpha_frac * 255)
            glow_r = self.radius * (1.6 + (1.0 - alpha_frac) * 2.2)
            py5.no_stroke()
            py5.fill(255, 255, 255, col_a)
            py5.ellipse(self.x, self.y, glow_r * 0.8, glow_r * 0.8)
            py5.fill(140, 70, 255, int(col_a * 0.65))
            py5.ellipse(self.x, self.y, glow_r * 2.0, glow_r * 2.0)

        elif self.ptype == "cherenkov":
            # Actinic ultraviolet / electric cyan plasma quantum
            col_a = int(alpha_frac * 190)
            py5.stroke(60, 230, 255, col_a)
            py5.stroke_weight(self.radius * 0.8)
            py5.point(self.x, self.y)
            if len(self.history) > 1:
                py5.stroke(160, 70, 255, int(col_a * 0.5))
                py5.stroke_weight(self.radius * 0.4)
                hx, hy = self.history[-2]
                py5.line(hx, hy, self.x, self.y)


particles = []
MAX_PARTICLES = 1300


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    py5.background(4, 5, 13)


def compute_josephson_state(t, frame_idx):
    """
    Computes the 2D electrodynamic state of relativistic fluxons in a Long Josephson Junction:
    - Multiple forward and backward traveling topological solitons (fluxons and antifluxons)
    - Relativistic Lorentz contraction gamma_L(v)
    - Magnetic field distribution B_z(x, y, t)
    - Trailing Cherenkov plasma wake waves
    - Periodic topological annihilation collision events creating radiant plasma breathers
    - Meissner screening supercurrents in the superconducting electrodes
    """
    # 1. Fluxon Trajectories and Kinematics
    # Period of cyclic motion across the junction
    cycle_time = 3.2
    phase_in_cycle = (t % cycle_time) / cycle_time

    # Pair 1: Primary head-on collision pair
    # Moves from boundaries x = +/- 3.5 toward collision center x = 0
    t_collision = 1.6
    dt_coll = (t % cycle_time) - t_collision
    speed_factor = 0.92  # Relativistic velocity v / c_bar ~ 0.92
    gamma_lorentz = 1.0 / np.sqrt(max(0.02, 1.0 - speed_factor**2))  # gamma ~ 2.55

    # Positions before and after collision
    if dt_coll < 0:
        # Accelerating towards center
        pos_fluxon_1 = 3.2 * (dt_coll / t_collision)
        pos_antifluxon_1 = -3.2 * (dt_coll / t_collision)
        annihilation_flash = 0.0
    else:
        # After collision: high-energy bound plasma breather pulsating at x=0
        # and re-emerging daughter fluxons
        breather_envelope = np.exp(-dt_coll * 2.2)
        pos_fluxon_1 = 3.2 * (dt_coll / t_collision)
        pos_antifluxon_1 = -3.2 * (dt_coll / t_collision)
        annihilation_flash = float(breather_envelope * np.cos(32.0 * dt_coll)**2)

    # Pair 2: Staggered secondary fluxon train
    pos_fluxon_2 = -3.5 + ((t * 1.8 + 1.2) % 7.0)
    pos_antifluxon_2 = 3.5 - ((t * 1.8 + 2.5) % 7.0)

    # 2. Magnetic Field Profile B_z(x, y, t) = d(phi)/dx
    # Tunnel barrier profile: Gaussian centered at y=0 with width BARRIER_HALF_HEIGHT
    barrier_envelope = np.exp(-(Y_grid / (BARRIER_HALF_HEIGHT * 0.85))**2)
    electrode_envelope = 1.0 - np.exp(-(np.maximum(0.0, np.abs(Y_grid) - BARRIER_HALF_HEIGHT) / 0.15)**2)

    # Soliton magnetic field cores: B_z ~ 2 * gamma / (cosh(gamma * (x - x_0) / lambda_J))
    def soliton_core(x_pos, gamma_L, sign=1.0):
        arg = np.clip(gamma_L * (X_grid - x_pos) / LAMBDA_J, -15.0, 15.0)
        return sign * (2.0 * gamma_L / np.cosh(arg))

    b_fluxon_1 = soliton_core(pos_fluxon_1, gamma_lorentz, sign=1.0)
    b_antifluxon_1 = soliton_core(pos_antifluxon_1, gamma_lorentz, sign=-1.0)
    b_fluxon_2 = soliton_core(pos_fluxon_2, gamma_lorentz * 0.8, sign=1.0)
    b_antifluxon_2 = soliton_core(pos_antifluxon_2, gamma_lorentz * 0.8, sign=-1.0)

    b_total = (b_fluxon_1 + b_antifluxon_1 + b_fluxon_2 + b_antifluxon_2) * barrier_envelope

    # 3. Relativistic Cherenkov Plasma Wake Waves
    # Trailing waves emitted behind each moving fluxon inside the barrier and electrodes
    cherenkov_k = 12.0
    cherenkov_waves = np.zeros_like(X_grid)
    for pos, dir_sign in [(pos_fluxon_1, -1.0), (pos_antifluxon_1, 1.0), (pos_fluxon_2, -1.0), (pos_antifluxon_2, 1.0)]:
        # Behind the fluxon
        wake_dist = (X_grid - pos) * dir_sign
        wake_mask = (wake_dist > 0.0) & (wake_dist < 2.5)
        wake_phase = cherenkov_k * wake_dist - 14.0 * t
        cherenkov_waves += np.where(
            wake_mask,
            0.35 * np.cos(wake_phase) * np.exp(-wake_dist * 0.9) * np.exp(-(Y_grid / 0.9)**2),
            0.0
        )

    # 4. Topological Annihilation Breather & Radiant Shock Rings
    annihilation_rings = np.zeros_like(X_grid)
    if annihilation_flash > 0.01:
        r_dist = np.sqrt(X_grid**2 + Y_grid**2)
        ring_phase = 22.0 * r_dist - 35.0 * dt_coll
        annihilation_rings = annihilation_flash * 1.5 * np.cos(ring_phase) * np.exp(-r_dist * 1.2)

    # 5. Meissner Screening Supercurrents J_super = curl(B_z) in Electrodes
    # Supercurrent flows along the surface of electrodes y = +/- BARRIER_HALF_HEIGHT
    supercurrent_density = np.abs(b_total) * np.exp(-np.abs(np.abs(Y_grid) - BARRIER_HALF_HEIGHT) / 0.25)

    # 6. Superconducting Electrode Boundaries (Niobium Metal Substrate)
    electrode_mask = (np.abs(Y_grid) >= BARRIER_HALF_HEIGHT).astype(np.float32)
    barrier_channel_mask = (np.abs(Y_grid) < BARRIER_HALF_HEIGHT).astype(np.float32)

    # 7. Surface Normal Calculation for 3D Chrome Shading
    relief_field = (
        np.abs(b_total) * 1.4 +
        supercurrent_density * 1.2 +
        cherenkov_waves * 0.7 +
        annihilation_rings * 1.0 +
        electrode_mask * 0.8
    )
    grad_y, grad_x = np.gradient(relief_field, dy, dx)
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
        b_total,
        supercurrent_density,
        cherenkov_waves,
        annihilation_rings,
        annihilation_flash,
        electrode_mask,
        barrier_channel_mask,
        diffuse1,
        diffuse2,
        specular1,
        specular2,
        pos_fluxon_1,
        pos_antifluxon_1
    )


def render_field_to_buffer(
    b_total,
    supercurrent_density,
    cherenkov_waves,
    annihilation_rings,
    annihilation_flash,
    electrode_mask,
    barrier_channel_mask,
    diffuse1,
    diffuse2,
    specular1,
    specular2
):
    """
    Composes the quantum superconducting color palette into the ARGB pixel buffer:
    - Background: Sub-Kelvin cryogenic vacuum void and niobium slate (#04050d, #101426)
    - Dominant: High-energy relativistic fluxon cores in incandescent amber, solar gold, and molten copper
    - Secondary: Trailing Cherenkov electromagnetic wakes and Josephson plasma waves in actinic ultraviolet and electric cyan
    - Accent: Annihilation flashes and specular singularity nodes in diamond-white and solar platinum
    """
    # Base background: Deep cryogenic vacuum void
    r_field = np.full((Ny, Nx), 4.0, dtype=np.float32)
    g_field = np.full((Ny, Nx), 5.0, dtype=np.float32)
    b_field = np.full((Ny, Nx), 13.0, dtype=np.float32)

    # Superconducting Niobium Electrodes (Deep Slate Indigo & Titanium Chrome)
    nb_r = electrode_mask * (16.0 + 35.0 * diffuse1)
    nb_g = electrode_mask * (20.0 + 45.0 * diffuse1)
    nb_b = electrode_mask * (40.0 + 75.0 * diffuse1)
    r_field += nb_r
    g_field += nb_g
    b_field += nb_b

    # Insulating Tunnel Oxide Barrier Channel (Deep Carbon Void)
    ch_glow = barrier_channel_mask * 15.0
    r_field += ch_glow * 0.4
    g_field += ch_glow * 0.5
    b_field += ch_glow * 1.1

    # Relativistic Magnetic Fluxon Cores (Incandescent Amber, Solar Gold, Molten Copper)
    flux_mag = np.clip(np.abs(b_total) / 2.2, 0.0, 1.8)
    gold_r = 255.0 * flux_mag + 50.0 * (flux_mag**2)
    gold_g = 175.0 * (flux_mag**1.3) + 70.0 * (flux_mag**2.5)
    gold_b = 35.0 * (flux_mag**2.2)

    r_field += gold_r
    g_field += gold_g
    b_field += gold_b

    # Meissner Screening Supercurrents (Molten Copper & Warm Bronze Sheaths)
    sc_norm = np.clip(supercurrent_density / 1.8, 0.0, 1.0)
    r_field += sc_norm * 180.0
    g_field += sc_norm * 95.0
    b_field += sc_norm * 25.0

    # Cherenkov Plasma Waves (Actinic Ultraviolet & Electric Cyan Interference Fringes)
    ch_pos = np.maximum(0.0, cherenkov_waves)
    r_field += ch_pos * 90.0
    g_field += ch_pos * 180.0
    b_field += ch_pos * 245.0

    ch_neg = np.maximum(0.0, -cherenkov_waves)
    r_field += ch_neg * 130.0
    g_field += ch_neg * 45.0
    b_field += ch_neg * 220.0

    # Topological Annihilation Breather & Radiant Rings (Blinding Plasma White & Iris Violet)
    ring_pos = np.maximum(0.0, annihilation_rings)
    r_field += ring_pos * 240.0
    g_field += ring_pos * 210.0
    b_field += ring_pos * 255.0

    # Annihilation Core Central Glint
    if annihilation_flash > 0.05:
        dist_c = np.sqrt(X_grid**2 + Y_grid**2)
        flash_core = annihilation_flash * np.exp(-(dist_c / 0.35)**2) * 255.0
        r_field += flash_core
        g_field += flash_core
        b_field += flash_core

    # Specular Chrome Glints (Incandescent Diamond-White & Solar Platinum)
    spec_total = specular1 * 1.1 + specular2 * 0.95
    r_field += spec_total * 255.0
    g_field += spec_total * 248.0
    b_field += spec_total * 235.0

    # Final Clipping and Transfer to Buffer
    pixel_buffer[..., 1] = np.clip(r_field, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g_field, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b_field, 0, 255).astype(np.uint8)


def draw_frame():
    frame = py5.frame_count
    t = float(frame) / float(FPS)

    # 1. Compute Continuum Electrodynamic State
    (
        b_total,
        supercurrent_density,
        cherenkov_waves,
        annihilation_rings,
        annihilation_flash,
        electrode_mask,
        barrier_channel_mask,
        diffuse1,
        diffuse2,
        specular1,
        specular2,
        pos_fluxon_1,
        pos_antifluxon_1
    ) = compute_josephson_state(t, frame)

    # 2. Render Continuum Fields to High-Precision ARGB Pixel Buffer
    render_field_to_buffer(
        b_total,
        supercurrent_density,
        cherenkov_waves,
        annihilation_rings,
        annihilation_flash,
        electrode_mask,
        barrier_channel_mask,
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

    # 4. Lagrangian Particle Dynamics (Cooper Supercurrents, Annihilation Sparks, Cherenkov Photons)
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
                # Meissner supercurrent vortex loop tracer in the electrodes
                chosen_fluxon_x = random.choice([pos_fluxon_1, pos_antifluxon_1])
                electrode_sign = 1.0 if random.random() < 0.5 else -1.0
                sim_x = chosen_fluxon_x + random.gauss(0.0, 0.35)
                sim_y = electrode_sign * (BARRIER_HALF_HEIGHT + random.uniform(0.05, 0.45))
                px, py = sim_to_screen(sim_x, sim_y)

                # Vortex circulation velocity
                circ_dir = -1.0 if electrode_sign > 0 else 1.0
                particles.append(CooperParticle(
                    px, py,
                    ptype="supercurrent",
                    vx=circ_dir * random.uniform(2.5, 6.0),
                    vy=random.gauss(0.0, 0.6),
                    life=random.uniform(40.0, 85.0),
                    radius=random.uniform(1.4, 2.6)
                ))

            elif roll < 0.75:
                # Cherenkov plasma wake photon in the barrier
                chosen_fluxon_x = random.choice([pos_fluxon_1, pos_antifluxon_1])
                trail_x = chosen_fluxon_x + random.uniform(-1.2, 1.2)
                sim_y = random.uniform(-BARRIER_HALF_HEIGHT * 0.9, BARRIER_HALF_HEIGHT * 0.9)
                px, py = sim_to_screen(trail_x, sim_y)
                particles.append(CooperParticle(
                    px, py,
                    ptype="cherenkov",
                    vx=random.uniform(-2.0, 2.0),
                    vy=random.uniform(-1.5, 1.5),
                    life=random.uniform(35.0, 75.0),
                    radius=random.uniform(1.2, 2.2)
                ))

            else:
                # High-energy annihilation spark burst at junction center during collision
                if annihilation_flash > 0.15:
                    sim_x = random.gauss(0.0, 0.25)
                    sim_y = random.gauss(0.0, 0.18)
                    px, py = sim_to_screen(sim_x, sim_y)
                    spark_speed = random.uniform(5.0, 11.5)
                    spark_ang = random.uniform(-np.pi, np.pi)
                    particles.append(CooperParticle(
                        px, py,
                        ptype="annihilation_spark",
                        vx=spark_speed * np.cos(spark_ang),
                        vy=spark_speed * np.sin(spark_ang),
                        life=random.uniform(20.0, 50.0),
                        radius=random.uniform(2.0, 4.2)
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
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Annihilation: {annihilation_flash:.2f} | Particles: {len(particles)}")

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

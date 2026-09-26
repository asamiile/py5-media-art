"""
kinetic_optomechanical_cavity_backaction_2d
Quantum optomechanics simulation of radiation-pressure dynamical backaction:
a micro-mechanical cantilever mirror coupled to a high-finesse Fabry-Pérot optical cavity,
generating self-sustained limit cycle phonon oscillations, breathing standing waves,
optical frequency comb sidebands, and photoelastic cantilever stress birefringence.

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

# Dual Specular Light Vectors for Micro-Optics Silicon & Dielectric Chrome Shading
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

# Physical Parameters of the Optomechanical Microcavity
X_LEFT_MIRROR = -2.2      # Fixed dielectric Bragg mirror position
X_RIGHT_BASE = 1.7        # Rest position of vibrating nano-membrane
OMEGA_M = 3.6             # Fundamental mechanical resonance frequency (rad/s)
GAMMA_M = 0.05            # Mechanical damping rate
KAPPA = 0.8               # Cavity optical linewidth / decay rate
DELTA_0 = 0.65            # Blue-detuned laser drive (instability regime)
G_0 = 1.4                 # Optomechanical coupling rate per displacement


class OptoParticle:
    """Lagrangian tracer particle: photon packet or acoustic phonon ripple."""
    def __init__(self, x, y, ptype="photon", vx=0.0, vy=0.0, life=60.0, radius=2.0):
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
        if len(self.history) > 5:
            self.history.pop(0)

        if self.ptype == "photon":
            # Fast, high-energy intra-cavity or transmitted laser photon
            self.x += self.vx
            self.y += self.vy
        elif self.ptype == "phonon":
            # Expanding acoustic phonon ripple in substrate
            self.x += self.vx
            self.y += self.vy
            self.radius += 0.05
        elif self.ptype == "spark":
            # Dielectric mirror surface ionization spark
            self.vx *= 0.93
            self.vy *= 0.93
            self.x += self.vx
            self.y += self.vy

    def draw(self, w, h):
        alpha_frac = max(0.0, min(1.0, self.life / self.max_life))
        pulse = 0.7 + 0.3 * np.sin(self.life * 0.25)

        if self.ptype == "photon":
            # Radiant ruby / crimson laser photon packet
            col_a = int(alpha_frac * 240 * pulse)
            py5.stroke(255, 60, 110, col_a)
            py5.stroke_weight(self.radius * (0.8 + 0.4 * alpha_frac))
            py5.point(self.x, self.y)

            if len(self.history) > 1:
                py5.stroke(255, 140, 170, int(col_a * 0.5))
                py5.stroke_weight(max(1.0, self.radius * 0.5))
                hx, hy = self.history[-2]
                py5.line(hx, hy, self.x, self.y)

        elif self.ptype == "phonon":
            # Phosphor emerald / mint acoustic quantum phonon
            col_a = int(alpha_frac * 190)
            py5.no_fill()
            py5.stroke(60, 245, 170, col_a)
            py5.stroke_weight(self.radius * 0.6)
            py5.ellipse(self.x, self.y, self.radius * 4.0, self.radius * 4.0)

        elif self.ptype == "spark":
            # Diamond-white specular cavity flash
            col_a = int(alpha_frac * 255)
            py5.no_stroke()
            py5.fill(255, 255, 255, col_a)
            py5.ellipse(self.x, self.y, self.radius * 1.2, self.radius * 1.2)
            py5.fill(160, 210, 255, int(col_a * 0.6))
            py5.ellipse(self.x, self.y, self.radius * 2.5, self.radius * 2.5)


particles = []
MAX_PARTICLES = 1400


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    py5.background(4, 6, 14)


def compute_optomechanical_state(t, frame_idx):
    """
    Simulates the non-linear coupled dynamical backaction of the optomechanical cavity:
    - Cantilever mechanical displacement x_m(t) exhibiting limit cycle growth
    - Intracavity photon field intensity |a(t)|^2 breathing and bursting on resonance
    - Optical standing wave interference fringes between Bragg mirrors
    - Transmitted and reflected sideband beams
    - Acoustic phonon waves propagating into the silicon substrate
    - Cantilever bending stress and photoelastic birefringence
    """
    # 1. Non-linear Mechanical Limit Cycle Dynamics
    # In blue detuning, optomechanical dynamical backaction drives exponential amplitude growth
    # that saturates into an optomechanical limit cycle
    growth_envelope = 1.0 - np.exp(-t * 0.35)
    limit_cycle_amp = 0.32 * growth_envelope
    mech_phase = OMEGA_M * t
    x_disp = limit_cycle_amp * np.sin(mech_phase)

    # Cantilever membrane profile: clamped at y = +/- 1.5, maximum displacement at center y = 0
    membrane_mask = np.clip(1.0 - (Y_grid / 1.5)**2, 0.0, 1.0)
    membrane_profile = x_disp * (membrane_mask**2)
    x_membrane = X_RIGHT_BASE + membrane_profile

    # 2. Cavity Optical Field & Detuning Resonance
    # Effective dynamic detuning Delta(t) = Delta_0 - G_0 * x_disp
    effective_detuning = DELTA_0 - G_0 * x_disp
    # Lorentzian cavity transmission resonance
    intracavity_intensity = 1.0 / (1.0 + (effective_detuning / (KAPPA * 0.5))**2)
    cavity_photon_amp = np.sqrt(intracavity_intensity)

    # 3. Spatial Optical Standing Wavefield E(x, y, t)
    # Cavity gap L(y, t) = x_membrane(y, t) - X_LEFT_MIRROR
    cavity_gap = np.maximum(0.2, x_membrane - X_LEFT_MIRROR)
    # Optical mode number m ~ 16 fringes across cavity
    m_mode = 16.0
    k_opt = m_mode * np.pi / cavity_gap

    # Gaussian transverse beam envelope (waist w_0 ~ 0.65)
    beam_waist = 0.65
    beam_envelope = np.exp(-(Y_grid / beam_waist)**2)

    # In-cavity mask (between left mirror and membrane)
    in_cavity = (X_grid >= X_LEFT_MIRROR) & (X_grid <= x_membrane)

    # High-frequency standing wave inside cavity
    phase_opt = k_opt * (X_grid - X_LEFT_MIRROR)
    standing_wave = np.sin(phase_opt)**2 * beam_envelope * cavity_photon_amp

    # External transmitted sideband laser beam (exiting right past the membrane)
    trans_mask = (X_grid > x_membrane) & (np.abs(Y_grid) < 1.6)
    k_trans = 14.0
    transmitted_wave = np.sin(k_trans * X_grid - 18.0 * t)**2 * beam_envelope * (cavity_photon_amp * 0.75)

    # External reflected pump laser beam (left of fixed mirror)
    refl_mask = (X_grid < X_LEFT_MIRROR) & (np.abs(Y_grid) < 1.6)
    reflected_wave = (0.5 + 0.5 * np.sin(k_trans * X_grid + 18.0 * t)) * beam_envelope * 0.6

    optical_field = np.zeros_like(X_grid)
    optical_field += np.where(in_cavity, standing_wave, 0.0)
    optical_field += np.where(trans_mask, transmitted_wave, 0.0)
    optical_field += np.where(refl_mask, reflected_wave, 0.0)

    # 4. Mechanical Structure (Bragg Mirrors & Cantilever Membrane)
    # Left Bragg mirror: multilayer periodic dielectric stacks
    left_bragg = np.zeros_like(X_grid)
    left_mirror_region = (X_grid >= X_LEFT_MIRROR - 0.35) & (X_grid <= X_LEFT_MIRROR) & (np.abs(Y_grid) < 1.5)
    if np.any(left_mirror_region):
        bragg_fringes = 0.5 + 0.5 * np.cos(38.0 * X_grid)
        left_bragg = np.where(left_mirror_region, bragg_fringes, 0.0)

    # Right Cantilever Membrane: compliant silicon nitride beam
    beam_thickness = 0.12
    cantilever_region = (np.abs(X_grid - x_membrane) <= beam_thickness * 0.5) & (np.abs(Y_grid) <= 1.5)
    cantilever_mask = np.where(cantilever_region, 1.0, 0.0)

    # Cantilever anchor frames at top and bottom
    anchors = ((np.abs(Y_grid) >= 1.45) & (np.abs(Y_grid) <= 1.85) & (X_grid >= X_LEFT_MIRROR - 0.5) & (X_grid <= X_RIGHT_BASE + 0.8)).astype(np.float32)

    # 5. Acoustic Phonon Radiation into Silicon Substrate (x > X_RIGHT_BASE)
    acoustic_phonons = np.zeros_like(X_grid)
    substrate_mask = X_grid >= X_RIGHT_BASE + 0.1
    for anchor_y in [-1.5, 0.0, 1.5]:
        dist_ph = np.sqrt((X_grid - (X_RIGHT_BASE + 0.1))**2 + (Y_grid - anchor_y)**2)
        ph_phase = 12.0 * dist_ph - OMEGA_M * t
        acoustic_phonons += np.where(
            substrate_mask,
            0.18 * np.sin(ph_phase) * np.exp(-dist_ph * 0.8) * (limit_cycle_amp / 0.32),
            0.0
        )

    # 6. Cantilever Photoelastic Birefringence Stress Fringes
    # Stress sigma(y) proportional to bending curvature ~ d^2(membrane_profile)/dy^2
    stress_field = np.abs(Y_grid) * (1.0 - (Y_grid / 1.5)**2) * (limit_cycle_amp / 0.32)
    birefringence = np.where(cantilever_region, np.sin(16.0 * stress_field)**2, 0.0)

    # 7. Surface Normal Calculation for 3D Chrome Shading
    relief_field = (
        optical_field * 1.5 +
        left_bragg * 1.2 +
        cantilever_mask * 1.8 +
        anchors * 1.4 +
        acoustic_phonons * 0.5
    )
    grad_y, grad_x = np.gradient(relief_field, dy, dx)
    inv_norm = 1.0 / np.sqrt(grad_x**2 + grad_y**2 + 1.0)
    nx_map = -grad_x * inv_norm
    ny_map = -grad_y * inv_norm
    nz_map = inv_norm

    # 8. Specular Highlights (Blinn-Phong)
    ndoth1 = np.maximum(0.0, nx_map * h1[0] + ny_map * h1[1] + nz_map * h1[2])
    ndoth2 = np.maximum(0.0, nx_map * h2[0] + ny_map * h2[1] + nz_map * h2[2])
    specular1 = ndoth1**38.0
    specular2 = ndoth2**52.0

    # 9. Diffuse Illuminations
    diffuse1 = np.maximum(0.0, nx_map * light1[0] + ny_map * light1[1] + nz_map * light1[2])
    diffuse2 = np.maximum(0.0, nx_map * light2[0] + ny_map * light2[1] + nz_map * light2[2])

    return (
        optical_field,
        intracavity_intensity,
        left_bragg,
        cantilever_mask,
        anchors,
        acoustic_phonons,
        birefringence,
        diffuse1,
        diffuse2,
        specular1,
        specular2,
        x_membrane,
        limit_cycle_amp
    )


def render_field_to_buffer(
    optical_field,
    intracavity_intensity,
    left_bragg,
    cantilever_mask,
    anchors,
    acoustic_phonons,
    birefringence,
    diffuse1,
    diffuse2,
    specular1,
    specular2
):
    """
    Composes the cold/precise optomechanical color palette into the ARGB pixel buffer:
    - Background: Cryogenic vacuum chamber obsidian void (#04060e)
    - Dominant: High-finesse circulating laser in radiant ruby crimson (#f82b60), rose, and amber
    - Secondary: Metallic silicon and dielectric Bragg mirrors in glacial ice (#dff4ff) and sapphire (#2d68f8)
    - Accent: Acoustic phonon wavefronts and resonance nodes in phosphor emerald mint (#36f4b0) & diamond-white
    """
    # Base background: Deep cryogenic vacuum void
    r_field = np.full((Ny, Nx), 4.0, dtype=np.float32)
    g_field = np.full((Ny, Nx), 6.0, dtype=np.float32)
    b_field = np.full((Ny, Nx), 14.0, dtype=np.float32)

    # Ambient subtle micro-cavity substrate gradations
    dist_origin = np.sqrt(X_grid**2 + Y_grid**2)
    ambient_substrate = np.exp(-dist_origin * 0.3) * 10.0
    r_field += ambient_substrate * 0.5
    g_field += ambient_substrate * 0.7
    b_field += ambient_substrate * 1.6

    # Micro-Fabricated Silicon Anchors & Substrate Frames (Deep Charcoal Sapphire)
    r_field += anchors * (35.0 + 30.0 * diffuse1)
    g_field += anchors * (45.0 + 40.0 * diffuse1)
    b_field += anchors * (75.0 + 60.0 * diffuse1)

    # Fixed Dielectric Bragg Mirror (Glacial Azure & Ice Platinum Multilayers)
    r_field += left_bragg * (110.0 + 80.0 * diffuse2)
    g_field += left_bragg * (160.0 + 90.0 * diffuse2)
    b_field += left_bragg * (240.0 + 40.0 * diffuse2)

    # Movable Cantilever Membrane & Photoelastic Stress Birefringence
    # Mechanical silicon nitride core
    cant_base = cantilever_mask * 140.0
    r_field += cant_base * 0.7
    g_field += cant_base * 0.85
    b_field += cant_base * 1.15

    # Photoelastic stress fringes (rainbow polariscopic birefringence on bending)
    r_field += birefringence * 180.0
    g_field += birefringence * 90.0
    b_field += birefringence * 210.0

    # Coherent Circulating & Transmitted Laser Field (Radiant Ruby Crimson, Rose, and Amber)
    opt_norm = np.clip(optical_field, 0.0, 1.8)
    ruby_r = 248.0 * opt_norm + 40.0 * (opt_norm**2)
    ruby_g = 43.0 * (opt_norm**1.5) + 80.0 * (opt_norm**3)
    ruby_b = 96.0 * (opt_norm**1.8)

    r_field += ruby_r
    g_field += ruby_g
    b_field += ruby_b

    # Acoustic Phonon Wavefronts (Phosphor Emerald Mint & Glacial Cyan)
    ph_pos = np.maximum(0.0, acoustic_phonons)
    r_field += ph_pos * 40.0
    g_field += ph_pos * 235.0
    b_field += ph_pos * 170.0

    # Specular Chrome Glints (Incandescent Diamond-White & Solar Platinum)
    spec_total = specular1 * 1.1 + specular2 * 0.95
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

    # 1. Compute Coupled Continuum Optomechanical State
    (
        optical_field,
        intracavity_intensity,
        left_bragg,
        cantilever_mask,
        anchors,
        acoustic_phonons,
        birefringence,
        diffuse1,
        diffuse2,
        specular1,
        specular2,
        x_membrane,
        limit_cycle_amp
    ) = compute_optomechanical_state(t, frame)

    # 2. Render Continuum Fields to High-Precision ARGB Pixel Buffer
    render_field_to_buffer(
        optical_field,
        intracavity_intensity,
        left_bragg,
        cantilever_mask,
        anchors,
        acoustic_phonons,
        birefringence,
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

    # 4. Lagrangian Optomechanical Particles (Photons, Phonons, Cavity Sparks)
    def sim_to_screen(sx, sy):
        px = (sx - x_coords[0]) / (x_coords[-1] - x_coords[0]) * py5.width
        py = (y_coords[-1] - sy) / (y_coords[-1] - y_coords[0]) * py5.height
        return px, py

    # Spawn new particles dynamically based on cavity resonance bursts
    if len(particles) < MAX_PARTICLES and frame < TOTAL_FRAMES - 30:
        spawn_budget = min(45, MAX_PARTICLES - len(particles))
        for _ in range(spawn_budget):
            roll = random.random()

            if roll < 0.45:
                # Intra-cavity & transmitted laser photon packets
                if random.random() < 0.6:
                    # Inside cavity bouncing between mirrors
                    sim_x = random.uniform(X_LEFT_MIRROR + 0.1, X_RIGHT_BASE - 0.1)
                    sim_y = random.gauss(0.0, 0.35)
                    px, py = sim_to_screen(sim_x, sim_y)
                    direction = 1.0 if random.random() < 0.5 else -1.0
                    particles.append(OptoParticle(
                        px, py,
                        ptype="photon",
                        vx=direction * random.uniform(4.5, 9.0),
                        vy=random.gauss(0.0, 0.4),
                        life=random.uniform(30.0, 70.0),
                        radius=random.uniform(1.4, 2.6)
                    ))
                else:
                    # Transmitted escaping sideband photons (racing to the right)
                    sim_x = float(x_membrane[Ny // 2, 0]) + random.uniform(0.05, 0.4)
                    sim_y = random.gauss(0.0, 0.45)
                    px, py = sim_to_screen(sim_x, sim_y)
                    particles.append(OptoParticle(
                        px, py,
                        ptype="photon",
                        vx=random.uniform(7.0, 12.0),
                        vy=random.gauss(0.0, 0.3),
                        life=random.uniform(40.0, 85.0),
                        radius=random.uniform(1.6, 2.8)
                    ))

            elif roll < 0.80:
                # Acoustic phonon emitted from cantilever into silicon substrate
                anchor_choice = random.choice([-1.5, 0.0, 1.5])
                sim_x = X_RIGHT_BASE + random.uniform(0.05, 0.25)
                sim_y = anchor_choice + random.gauss(0.0, 0.2)
                px, py = sim_to_screen(sim_x, sim_y)
                particles.append(OptoParticle(
                    px, py,
                    ptype="phonon",
                    vx=random.uniform(1.5, 4.2),
                    vy=random.uniform(-1.8, 1.8),
                    life=random.uniform(45.0, 95.0),
                    radius=random.uniform(1.2, 2.4)
                ))

            else:
                # High-energy cavity dielectric mirror spark during peak resonance
                if intracavity_intensity > 0.75:
                    on_left = random.random() < 0.5
                    sim_x = X_LEFT_MIRROR if on_left else float(x_membrane[Ny // 2, 0])
                    sim_y = random.uniform(-0.8, 0.8)
                    px, py = sim_to_screen(sim_x, sim_y)
                    spark_speed = random.uniform(2.5, 6.0)
                    spark_ang = random.uniform(-np.pi, np.pi)
                    particles.append(OptoParticle(
                        px, py,
                        ptype="spark",
                        vx=spark_speed * np.cos(spark_ang),
                        vy=spark_speed * np.sin(spark_ang),
                        life=random.uniform(20.0, 45.0),
                        radius=random.uniform(1.8, 3.8)
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
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Intracavity: {intracavity_intensity:.2f} | Particles: {len(particles)}")

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

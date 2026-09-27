"""
kinetic_whispering_gallery_kerr_soliton_microcomb_2d
2D integrated photonics simulation of a high-Q Whispering Gallery Mode (WGM)
optical microtoroid resonator coupled to a tapered bus waveguide:
evanescent optical tunneling, total internal reflection, four-wave mixing (FWM),
modulation instability (Turing rolls), dissipative Kerr soliton (DKS) formation
via Lugiato-Lefever dynamics, and prismatic optical frequency microcomb emission.

1920x1080 @ 60fps, 900 frames (15 seconds).
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
SIZE = PREVIEW_SIZE

# Spatial Simulation Grid (16:9 aspect ratio, 960x540 grid)
Nx, Ny = 960, 540
x_coords = np.linspace(-3.2, 3.2, Nx, dtype=np.float32)
y_coords = np.linspace(-1.8, 1.8, Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
dx = float(x_coords[1] - x_coords[0])
dy = float(y_coords[1] - y_coords[0])

# Geometry of Microphotonic Resonator & Tapered Waveguide
RES_X0, RES_Y0 = 0.0, -0.22      # Center of circular microtoroid
R_TOROID = 1.32                  # Outer rim radius
TOROID_WIDTH = 0.22              # Toroidal rim thickness
WG_Y = 1.18                      # Y position of bus waveguide
WG_HALF_WIDTH = 0.065            # Half-width of bus waveguide

# Polar coordinates relative to microtoroid center
R_res = np.sqrt((X_grid - RES_X0)**2 + (Y_grid - RES_Y0)**2)
Theta_res = np.arctan2(Y_grid - RES_Y0, X_grid - RES_X0)

# Dual Specular Light Vectors for Dielectric Silica Glass Chrome Shading
light1 = np.array([0.55, -0.65, 0.52], dtype=np.float32)
light1 /= np.linalg.norm(light1)
light2 = np.array([-0.50, 0.58, 0.64], dtype=np.float32)
light2 /= np.linalg.norm(light2)
view_vec = np.array([0.0, 0.0, 1.0], dtype=np.float32)
h1 = (light1 + view_vec) / np.linalg.norm(light1 + view_vec)
h2 = (light2 + view_vec) / np.linalg.norm(light2 + view_vec)

# ARGB pixel buffer for py5 (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255


class Photon:
    """Lagrangian photon wavepacket or Rayleigh scattering spark."""
    def __init__(self, x, y, ptype="waveguide", vx=0.0, vy=0.0, life=90.0, radius=2.5, color_rgba=None):
        self.x = float(x)
        self.y = float(y)
        self.ptype = ptype
        self.vx = float(vx)
        self.vy = float(vy)
        self.life = float(life)
        self.max_life = float(life)
        self.radius = float(radius)
        self.color_rgba = color_rgba or (0, 240, 255, 200)
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

        if self.ptype == "waveguide":
            # Propagating down the bus waveguide
            self.x += self.vx
            self.y += self.vy
        elif self.ptype == "soliton":
            # Circulating inside the Whispering Gallery Mode rim
            dx_c = self.x - RES_X0
            dy_c = self.y - RES_Y0
            r_c = np.sqrt(dx_c**2 + dy_c**2)
            angle = np.arctan2(dy_c, dx_c)
            # Angular velocity
            d_angle = 0.085
            new_angle = angle + d_angle
            # Maintain radial confinement along R_TOROID
            r_target = R_TOROID - 0.04
            new_r = 0.92 * r_c + 0.08 * r_target
            self.x = RES_X0 + new_r * np.cos(new_angle)
            self.y = RES_Y0 + new_r * np.sin(new_angle)
        elif self.ptype == "comb":
            # Dispersive out-coupled comb emission
            self.vx *= 1.01
            self.vy *= 1.01
            self.x += self.vx
            self.y += self.vy


particles = []


def compute_microcomb_state(t, frame):
    """
    Vectorized computation of continuous electromagnetic fields:
    1. Bus waveguide pump laser field
    2. Evanescent optical coupling bridge
    3. Whispering Gallery Mode (WGM) radial Bessel distribution
    4. Lugiato-Lefever Kerr soliton non-linear dynamics:
       - Phase 1 (0-4.5s): CW linear resonance
       - Phase 2 (4.5-8.5s): Modulation instability (Turing roll pattern)
       - Phase 3 (8.5-12.0s): Dissipative Kerr Soliton (DKS) pulse lock
       - Phase 4 (12.0-15.0s): Frequency comb out-coupling
    5. Specular dielectric silica surface optics
    """
    # 1. Bus Waveguide Pump Laser Field
    k_pump = 18.0
    omega_pump = 14.0
    wg_dist = np.abs(Y_grid - WG_Y)
    wg_mode = np.exp(-(wg_dist**2) / (2.0 * WG_HALF_WIDTH**2))
    e_pump = np.cos(k_pump * X_grid - omega_pump * t) * wg_mode

    # 2. Evanescent Coupling Bridge
    gap_dist = np.sqrt(X_grid**2 + (Y_grid - (WG_Y - WG_HALF_WIDTH))**2)
    evanescent_coupling = np.exp(-gap_dist / 0.16) * (np.abs(X_grid) < 0.6)

    # 3. Whispering Gallery Mode Radial Bessel Profile
    radial_dist = np.abs(R_res - (R_TOROID - TOROID_WIDTH * 0.45))
    wgm_radial_profile = np.exp(-(radial_dist**2) / (2.0 * (TOROID_WIDTH * 0.42)**2))

    # Silica Toroid Material Boundary Relief
    toroid_mask = np.exp(-((R_res - R_TOROID)**2) / (2.0 * (TOROID_WIDTH * 0.9)**2))

    # 4. Azimuthal Nonlinear Kerr Field Evolution Psi(theta, t)
    m_res = 38.0  # Azimuthal mode number
    omega_res = 12.0

    if t <= 4.5:
        # Phase 1: Continuous-Wave (CW) resonance
        coupling_gain = min(1.0, t / 2.5)
        psi_azimuthal = np.cos(m_res * Theta_res - omega_res * t) * coupling_gain
        soliton_intensity = np.zeros_like(Theta_res)
    elif t <= 8.5:
        # Phase 2: Modulation Instability (Turing roll necklace)
        tau_mi = (t - 4.5) / 4.0
        roll_modes = (
            np.cos(m_res * Theta_res - omega_res * t) +
            0.65 * tau_mi * np.cos((m_res + 4.0) * Theta_res - omega_res * 1.08 * t) +
            0.65 * tau_mi * np.cos((m_res - 4.0) * Theta_res - omega_res * 0.92 * t)
        )
        psi_azimuthal = roll_modes
        soliton_intensity = np.abs(roll_modes)**2 * tau_mi * 0.5
    else:
        # Phase 3 & 4: Dissipative Kerr Soliton (DKS) Pulse Lock
        tau_sol = min(1.0, (t - 8.5) / 2.0)
        # Two localized bright solitons orbiting at group velocity v_g
        v_g = 6.2
        theta_sol1 = np.mod(Theta_res - v_g * t, 2.0 * np.pi) - np.pi
        theta_sol2 = np.mod(Theta_res - v_g * t - np.pi, 2.0 * np.pi) - np.pi
        w_sol = 0.22

        sol1 = 1.0 / np.cosh(theta_sol1 / w_sol)
        sol2 = 0.85 / np.cosh(theta_sol2 / w_sol)
        soliton_intensity = (sol1**2 + sol2**2) * tau_sol

        carrier = np.cos(m_res * Theta_res - omega_res * t * 1.4)
        psi_azimuthal = (1.0 - tau_sol * 0.7) * carrier + 2.8 * (sol1 + sol2) * carrier

    # Resonator Internal Optical Field
    e_resonator = psi_azimuthal * wgm_radial_profile

    # 5. Out-Coupled Prismatic Frequency Comb Rays (Expanding into substrate)
    comb_field = np.zeros_like(R_res)
    if t > 8.0:
        t_comb = t - 8.0
        comb_mask = (R_res < (R_TOROID - TOROID_WIDTH * 0.8))
        comb_waves = np.sin(20.0 * R_res + Theta_res * 8.0 - t_comb * 8.0)
        comb_field = np.exp(-((R_res - 0.7)**2) / 0.18) * (1.0 + 0.5 * comb_waves) * comb_mask * min(1.0, t_comb / 2.0)

    # 6. Composite Optical Height Map for 3D Specular Shading
    relief_field = (
        toroid_mask * 1.4 +
        wg_mode * 1.1 +
        np.abs(e_resonator) * 1.2 +
        soliton_intensity * 2.2 +
        evanescent_coupling * 0.75 +
        comb_field * 0.5
    )

    # 7. Surface Normal Calculation
    grad_y, grad_x = np.gradient(relief_field, dy, dx)
    inv_norm = 1.0 / np.sqrt(grad_x**2 + grad_y**2 + 1.0)
    nx_map = -grad_x * inv_norm
    ny_map = -grad_y * inv_norm
    nz_map = inv_norm

    # 8. Specular Highlights (Blinn-Phong)
    ndoth1 = np.maximum(0.0, nx_map * h1[0] + ny_map * h1[1] + nz_map * h1[2])
    ndoth2 = np.maximum(0.0, nx_map * h2[0] + ny_map * h2[1] + nz_map * h2[2])
    specular1 = ndoth1**40.0
    specular2 = ndoth2**54.0

    diffuse1 = np.maximum(0.0, nx_map * light1[0] + ny_map * light1[1] + nz_map * light1[2])
    diffuse2 = np.maximum(0.0, nx_map * light2[0] + ny_map * light2[1] + nz_map * light2[2])

    return (
        e_pump,
        wg_mode,
        e_resonator,
        wgm_radial_profile,
        toroid_mask,
        soliton_intensity,
        evanescent_coupling,
        comb_field,
        diffuse1,
        diffuse2,
        specular1,
        specular2
    )


def render_field_to_buffer(
    e_pump,
    wg_mode,
    e_resonator,
    wgm_radial_profile,
    toroid_mask,
    soliton_intensity,
    evanescent_coupling,
    comb_field,
    diffuse1,
    diffuse2,
    specular1,
    specular2
):
    """
    Composes electromagnetic fields into the ARGB pixel buffer using the 4-color palette:
    1. Circulating Kerr Solitons & Core Ring: Luminous Glacial Cyan (#00f0ff) & Sapphire Blue (#0077b6)
    2. Evanescent Coupling & Microcomb Fringes: Laser Magenta (#ff007f) & Actinic Amethyst (#9d4edd)
    3. Dielectric Silica Specular Chrome: Diamond White (#ffffff) & Solar Platinum (#fff3b0)
    4. Photonic Chip Substrate Void: Deep Obsidian Indigo (#02050e, #0a1228)
    """
    # Background: Midnight obsidian indigo photonic substrate
    r_norm = np.clip(np.sqrt(X_grid**2 + Y_grid**2) / 3.2, 0.0, 1.0)
    r_field = 2.0 + 8.0 * r_norm
    g_field = 5.0 + 12.0 * r_norm
    b_field = 14.0 + 26.0 * r_norm

    # 1. Silica Microtoroid Structure (Deep Sapphire & Niobium Glass)
    toroid_norm = np.clip(toroid_mask * 0.9, 0.0, 1.2)
    diff_total = diffuse1 * 0.7 + diffuse2 * 0.45
    r_field += toroid_norm * (8.0 + diff_total * 40.0)
    g_field += toroid_norm * (40.0 + diff_total * 90.0)
    b_field += toroid_norm * (110.0 + diff_total * 135.0)

    # 2. Bus Waveguide Pump Laser (Luminous Electric Cyan Stream)
    pump_norm = np.clip(wg_mode * (0.6 + 0.4 * np.abs(e_pump)), 0.0, 1.5)
    r_field += pump_norm * 0.0
    g_field += pump_norm * 220.0
    b_field += pump_norm * 255.0

    # 3. Whispering Gallery Mode Resonator Field (Cyan & Sapphire Resonance)
    res_norm = np.clip(np.abs(e_resonator) * 1.1, 0.0, 2.2)
    r_field += res_norm * 10.0
    g_field += res_norm * 210.0
    b_field += res_norm * 255.0

    # 4. Evanescent Coupling Junction (Laser Magenta & Violet Tunneling)
    evan_norm = np.clip(evanescent_coupling * 1.5, 0.0, 2.0)
    r_field += evan_norm * 255.0
    g_field += evan_norm * 20.0
    b_field += evan_norm * 160.0

    # 5. Dissipative Kerr Soliton Pulse Core (Incandescent Solar White-Cyan Peak)
    sol_norm = np.clip(soliton_intensity * 1.25, 0.0, 3.5)
    r_field += sol_norm * 240.0
    g_field += sol_norm * 255.0
    b_field += sol_norm * 255.0

    # 6. Frequency Microcomb Dispersion Fan (Actinic Amethyst & Laser Rose)
    comb_norm = np.clip(comb_field * 1.3, 0.0, 1.8)
    r_field += comb_norm * 190.0
    g_field += comb_norm * 45.0
    b_field += comb_norm * 230.0

    # 7. Dual Blinn-Phong Specular Glass Chrome Glints
    spec_total = specular1 * 1.25 + specular2 * 1.05
    r_field += spec_total * 255.0
    g_field += spec_total * 250.0
    b_field += spec_total * 240.0

    # Final Transfer to Buffer
    pixel_buffer[..., 1] = np.clip(r_field, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g_field, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b_field, 0, 255).astype(np.uint8)


def update_and_draw_particles(t):
    """Update and render Lagrangian photon wavepackets and scattering sparks."""
    global particles

    # Spawn waveguide pump photons
    if len(particles) < 2200:
        for _ in range(6):
            particles.append(
                Photon(
                    -3.2,
                    WG_Y + random.uniform(-WG_HALF_WIDTH * 0.8, WG_HALF_WIDTH * 0.8),
                    ptype="waveguide",
                    vx=random.uniform(0.045, 0.065),
                    vy=0.0,
                    life=random.uniform(80, 120),
                    radius=random.uniform(1.8, 3.2),
                    color_rgba=(0, 240, 255, 210)
                )
            )

    # Spawn circulating soliton photons
    if t > 3.0 and len(particles) < 2200:
        for _ in range(7):
            angle = random.uniform(-np.pi, np.pi)
            r = R_TOROID + random.uniform(-TOROID_WIDTH * 0.4, TOROID_WIDTH * 0.2)
            particles.append(
                Photon(
                    RES_X0 + r * np.cos(angle),
                    RES_Y0 + r * np.sin(angle),
                    ptype="soliton",
                    life=random.uniform(70, 140),
                    radius=random.uniform(2.0, 3.6),
                    color_rgba=(180, 245, 255, 230)
                )
            )

    # Spawn out-coupled frequency comb sparks
    if t > 8.5:
        for _ in range(5):
            angle = random.uniform(-np.pi, np.pi)
            speed = random.uniform(0.012, 0.028)
            particles.append(
                Photon(
                    RES_X0 + (R_TOROID - 0.1) * np.cos(angle),
                    RES_Y0 + (R_TOROID - 0.1) * np.sin(angle),
                    ptype="comb",
                    vx=-speed * np.cos(angle),
                    vy=-speed * np.sin(angle),
                    life=random.uniform(40, 80),
                    radius=random.uniform(2.2, 4.2),
                    color_rgba=(255, 30, 160, 200)
                )
            )

    # Transform coordinates to screen pixels
    scale_x = float(py5.width) / 6.4
    scale_y = float(py5.height) / 3.6
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

        sx = cx + p.x * scale_x
        sy = cy - p.y * scale_y

        if not (-50 <= sx <= py5.width + 50 and -50 <= sy <= py5.height + 50):
            continue

        life_ratio = p.life / p.max_life
        r, g, b, base_alpha = p.color_rgba
        alpha = base_alpha * life_ratio

        # Particle streak
        if len(p.history) >= 2:
            py5.stroke(r, g, b, alpha * 0.6)
            py5.stroke_weight(p.radius * 0.65)
            for i in range(len(p.history) - 1):
                x1, y1 = p.history[i]
                x2, y2 = p.history[i + 1]
                py5.line(cx + x1 * scale_x, cy - y1 * scale_y, cx + x2 * scale_x, cy - y2 * scale_y)
            py5.no_stroke()

        py5.fill(r, g, b, alpha)
        py5.circle(sx, sy, p.radius)

        py5.fill(r, g, b, alpha * 0.25)
        py5.circle(sx, sy, p.radius * 2.6)

    particles = alive_particles
    py5.blend_mode(py5.BLEND)


def draw_frame():
    frame = py5.frame_count
    t = float(frame) / float(FPS)

    # 1. Compute Continuum Microcomb State
    (
        e_pump,
        wg_mode,
        e_resonator,
        wgm_radial_profile,
        toroid_mask,
        soliton_intensity,
        evanescent_coupling,
        comb_field,
        diffuse1,
        diffuse2,
        specular1,
        specular2
    ) = compute_microcomb_state(t, frame)

    # 2. Render Continuum Fields to High-Precision ARGB Pixel Buffer
    render_field_to_buffer(
        e_pump,
        wg_mode,
        e_resonator,
        wgm_radial_profile,
        toroid_mask,
        soliton_intensity,
        evanescent_coupling,
        comb_field,
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

    # 4. Render Lagrangian Particles
    update_and_draw_particles(t)

    # 5. Save Current Frame to Disk Cache
    frame_path = FRAMES_DIR / f"frame-{frame:04d}.png"
    py5.save_frame(str(frame_path))

    # Save preview image at peak soliton locking (frame 570, t ~ 9.5s)
    if frame == 570:
        preview_path = SKETCH_DIR / PREVIEW_FILENAME
        py5.save_frame(str(preview_path))
        print(f"[Preview Saved] Soliton lock preview captured: {preview_path}")

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

        # Fallback preview if frame 570 didn't trigger
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

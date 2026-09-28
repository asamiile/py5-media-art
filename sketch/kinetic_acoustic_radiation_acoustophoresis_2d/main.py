"""
kinetic_acoustic_radiation_acoustophoresis_2d
Microfluidic ultrasonic acoustophoresis simulation:
acoustic radiation force (Gor'kov potential gradient), standing wave pressure nodal bands,
boundary-layer Rayleigh acoustic streaming micro-vortex lattices, dual-contrast particle separation,
and Blinn-Phong specular quartz microchannel surface optics.

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

# Dual Specular Light Vectors for Crystalline Quartz Microchip Chrome Shading
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

# Physical Parameters of the Microchannel & Acoustic Resonator
CHANNEL_HALF_WIDTH = 3.5    # Channel length along x
CHANNEL_HALF_HEIGHT = 1.45   # Channel height along y
K_X = 2.4                   # Longitudinal acoustic wavenumber (nodes along x)
K_Y = 1.35                  # Transverse acoustic wavenumber (nodes along y)


class Microbead:
    """Lagrangian micro-particle subjected to Gor'kov acoustic radiation force and Rayleigh streaming."""
    def __init__(self, x, y, ptype="positive", vx=0.0, vy=0.0, life=120.0, radius=2.2):
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

    def update(self, fx_rad, fy_rad, us_flow, vs_flow):
        self.life -= 1.0
        if self.life <= 0.0:
            self.is_dead = True
            return

        self.history.append((self.x, self.y))
        if len(self.history) > 6:
            self.history.pop(0)

        if self.ptype == "positive":
            # Dense bead: dominated by radiation force pushing into nodal lines, minor drag
            self.vx = 0.75 * self.vx + 0.25 * (fx_rad * 4.5 + us_flow * 0.4)
            self.vy = 0.75 * self.vy + 0.25 * (fy_rad * 4.5 + vs_flow * 0.4)
        elif self.ptype == "negative":
            # Negative contrast: trapped in Rayleigh streaming whirlpools, pushed to antinodes
            self.vx = 0.82 * self.vx + 0.18 * (-fx_rad * 2.0 + us_flow * 1.8)
            self.vy = 0.82 * self.vy + 0.18 * (-fy_rad * 2.0 + vs_flow * 1.8)
        elif self.ptype == "spark":
            # Piezoelectric transducer acoustic cavitation spark
            self.vx *= 0.92
            self.vy *= 0.92

        self.x += self.vx
        self.y += self.vy

    def draw(self, w, h):
        alpha_frac = max(0.0, min(1.0, self.life / self.max_life))
        pulse = 0.7 + 0.3 * np.sin(self.life * 0.25)

        if self.ptype == "positive":
            # Fluorescent jade green / glacial mint focused bead
            col_a = int(alpha_frac * 220 * pulse)
            py5.stroke(10, 255, 160, col_a)
            py5.stroke_weight(self.radius * (0.8 + 0.4 * alpha_frac))
            py5.point(self.x, self.y)

            if len(self.history) > 1:
                py5.stroke(0, 200, 140, int(col_a * 0.5))
                py5.stroke_weight(max(1.0, self.radius * 0.55))
                hx, hy = self.history[-2]
                py5.line(hx, hy, self.x, self.y)

        elif self.ptype == "negative":
            # Electric violet / deep iris streaming bead
            col_a = int(alpha_frac * 190)
            py5.stroke(180, 80, 255, col_a)
            py5.stroke_weight(self.radius * 0.85)
            py5.point(self.x, self.y)

            if len(self.history) > 2:
                py5.no_fill()
                py5.stroke(130, 40, 240, int(col_a * 0.4))
                py5.stroke_weight(max(1.0, self.radius * 0.45))
                py5.begin_shape()
                for hx, hy in self.history:
                    py5.vertex(hx, hy)
                py5.end_shape()

        elif self.ptype == "spark":
            # Diamond-white acoustic pressure node spark
            col_a = int(alpha_frac * 255)
            glow_r = self.radius * (1.6 + (1.0 - alpha_frac) * 2.0)
            py5.no_stroke()
            py5.fill(255, 255, 255, col_a)
            py5.ellipse(self.x, self.y, glow_r * 0.8, glow_r * 0.8)
            py5.fill(255, 200, 60, int(col_a * 0.65))
            py5.ellipse(self.x, self.y, glow_r * 1.8, glow_r * 1.8)


particles = []
MAX_PARTICLES = 1400


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    py5.background(3, 8, 16)


def compute_acoustophoresis_state(t, frame_idx):
    """
    Computes the 2D ultrasonic acoustophoresis wavefield and hydrodynamic streaming state:
    - 2D standing acoustic pressure field p_1(x, y, t)
    - Gor'kov acoustic radiation potential U(x, y) and radiation force F_rad = -grad(U)
    - Boundary-layer Rayleigh acoustic streaming vortex streamfunction psi_s
    - Crystalline microfluidic quartz channel boundary walls
    - Surface normals and Blinn-Phong specular shading
    """
    # Channel geometric mask
    in_channel = (np.abs(X_grid) <= CHANNEL_HALF_WIDTH) & (np.abs(Y_grid) <= CHANNEL_HALF_HEIGHT)
    channel_mask = in_channel.astype(np.float32)

    # Wall frames (Quartz & Silicon Chip Carrier)
    walls = 1.0 - channel_mask

    # 1. Ultrasonic Standing Acoustic Pressure Field
    # Phase modulation over time simulates slight frequency drift and dynamic trapping
    omega_sound = 4.2
    freq_drift = 0.04 * np.sin(0.4 * t)
    kx_eff = K_X * (1.0 + freq_drift)
    ky_eff = K_Y

    # Primary standing wave modes
    p_wave = (
        np.cos(kx_eff * X_grid) * np.cos(ky_eff * Y_grid) * np.sin(omega_sound * t) +
        0.35 * np.cos(2.0 * kx_eff * X_grid) * np.sin(omega_sound * t * 1.5 + 0.8)
    ) * channel_mask

    # Time-averaged acoustic energy density <p_1^2>
    p_energy = (
        np.cos(kx_eff * X_grid)**2 * np.cos(ky_eff * Y_grid)**2 +
        0.25 * np.cos(2.0 * kx_eff * X_grid)**2
    ) * channel_mask

    # 2. Gor'kov Acoustic Radiation Potential U(x, y)
    # Dense particles (Phi > 0) are attracted to pressure nodes where p_energy is minimal
    # Acoustic radiation force F_rad ~ -grad(U) ~ -sin(2*kx*x)
    fx_rad_field = -np.sin(2.0 * kx_eff * X_grid) * np.cos(ky_eff * Y_grid)**2 * channel_mask
    fy_rad_field = -np.sin(2.0 * ky_eff * Y_grid) * np.cos(kx_eff * X_grid)**2 * channel_mask

    # 3. Rayleigh Boundary-Layer Acoustic Streaming Vortices
    # Streamfunction psi_s ~ -sin(2*kx*x) * sin(2*ky*y)
    stream_psi = -np.sin(2.0 * kx_eff * X_grid) * np.sin(2.0 * ky_eff * Y_grid) * channel_mask
    # Streaming velocity u_s = d(psi)/dy, v_s = -d(psi)/dx
    us_field = -2.0 * ky_eff * np.sin(2.0 * kx_eff * X_grid) * np.cos(2.0 * ky_eff * Y_grid) * channel_mask
    vs_field = 2.0 * kx_eff * np.cos(2.0 * kx_eff * X_grid) * np.sin(2.0 * ky_eff * Y_grid) * channel_mask

    # Streaming vorticity magnitude |omega_s|
    vorticity_streaming = np.abs(np.cos(2.0 * kx_eff * X_grid) * np.cos(2.0 * ky_eff * Y_grid)) * channel_mask

    # 4. Total Optical Density & Surface Relief Map
    relief_field = (
        p_energy * 1.5 +
        vorticity_streaming * 1.2 +
        walls * 2.2 +
        np.abs(p_wave) * 0.6
    )

    # 5. Surface Normal Calculation for 3D Chrome Shading
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
        p_wave,
        p_energy,
        fx_rad_field,
        fy_rad_field,
        us_field,
        vs_field,
        vorticity_streaming,
        walls,
        channel_mask,
        diffuse1,
        diffuse2,
        specular1,
        specular2,
        kx_eff,
        ky_eff
    )


def render_field_to_buffer(
    p_wave,
    p_energy,
    vorticity_streaming,
    walls,
    channel_mask,
    diffuse1,
    diffuse2,
    specular1,
    specular2
):
    """
    Composes the crystalline laboratory microfluidics color palette into the ARGB pixel buffer:
    - Background: Quartz microchannel obsidian void (#030810) and midnight slate (#0a1828)
    - Dominant: Ultrasonic standing wave pressure nodes in fluorescent jade green (#00ff9d) & glacial mint (#80ffcc)
    - Secondary: Rayleigh acoustic streaming whirlpools in electric violet (#7b2cbf) & deep iris (#9d4edd)
    - Accent: Trapped focus lines & acoustic flash nodes in diamond-white (#ffffff) and solar amber (#ffb703)
    """
    # Base background: Deep quartz substrate
    r_field = np.full((Ny, Nx), 3.0, dtype=np.float32)
    g_field = np.full((Ny, Nx), 8.0, dtype=np.float32)
    b_field = np.full((Ny, Nx), 18.0, dtype=np.float32)

    # Ambient microchannel substrate gradation
    dist_c = np.sqrt(X_grid**2 + Y_grid**2)
    ambient_substrate = np.exp(-dist_c * 0.35) * 10.0
    r_field += ambient_substrate * 0.4
    g_field += ambient_substrate * 0.7
    b_field += ambient_substrate * 1.5

    # Silicon & Quartz Channel Walls (Deep Midnight Slate & Platinum Rails)
    r_field += walls * (18.0 + 35.0 * diffuse1)
    g_field += walls * (30.0 + 45.0 * diffuse1)
    b_field += walls * (55.0 + 70.0 * diffuse1)

    # Ultrasonic Pressure Energy <p_1^2> (Fluorescent Jade Green & Glacial Mint Nodal Bands)
    # Energy peaks indicate antinodes; valleys indicate nodal lines where particles collect
    p_norm = np.clip(p_energy, 0.0, 1.8)
    jade_r = p_norm * (15.0 + 20.0 * diffuse2)
    jade_g = p_norm * (245.0 + 40.0 * diffuse2)
    jade_b = p_norm * (155.0 + 30.0 * diffuse2)
    r_field += jade_r * channel_mask
    g_field += jade_g * channel_mask
    b_field += jade_b * channel_mask

    # Rayleigh Acoustic Streaming Vortices (Electric Violet & Deep Iris Whirlpools)
    vort_norm = np.clip(vorticity_streaming * 1.3, 0.0, 1.5)
    r_field += vort_norm * 140.0 * channel_mask
    g_field += vort_norm * 45.0 * channel_mask
    b_field += vort_norm * 220.0 * channel_mask

    # Instantaneous Standing Wavefront Glint
    wave_glint = np.abs(p_wave) * 45.0 * channel_mask
    r_field += wave_glint * 0.6
    g_field += wave_glint * 1.0
    b_field += wave_glint * 0.9

    # Specular Quartz Glass Chrome Glints
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

    # 1. Compute Continuum Acoustophoresis State
    (
        p_wave,
        p_energy,
        fx_rad_field,
        fy_rad_field,
        us_field,
        vs_field,
        vorticity_streaming,
        walls,
        channel_mask,
        diffuse1,
        diffuse2,
        specular1,
        specular2,
        kx_eff,
        ky_eff
    ) = compute_acoustophoresis_state(t, frame)

    # 2. Render Continuum Fields to High-Precision ARGB Pixel Buffer
    render_field_to_buffer(
        p_wave,
        p_energy,
        vorticity_streaming,
        walls,
        channel_mask,
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

    # 4. Lagrangian Particle Dynamics (Dual-Contrast Microbeads & Acoustic Sparks)
    def sim_to_screen(sx, sy):
        px = (sx - x_coords[0]) / (x_coords[-1] - x_coords[0]) * py5.width
        py = (y_coords[-1] - sy) / (y_coords[-1] - y_coords[0]) * py5.height
        return px, py

    # Spawn particles dynamically inside the channel
    if len(particles) < MAX_PARTICLES and frame < TOTAL_FRAMES - 30:
        spawn_budget = min(45, MAX_PARTICLES - len(particles))
        for _ in range(spawn_budget):
            roll = random.random()

            sim_x = random.uniform(-CHANNEL_HALF_WIDTH * 0.95, CHANNEL_HALF_WIDTH * 0.95)
            sim_y = random.uniform(-CHANNEL_HALF_HEIGHT * 0.92, CHANNEL_HALF_HEIGHT * 0.92)
            px, py = sim_to_screen(sim_x, sim_y)

            if roll < 0.55:
                # Dense positive-contrast microbead (focuses into jade green nodal lines)
                particles.append(Microbead(
                    px, py,
                    ptype="positive",
                    vx=random.uniform(-0.5, 0.5),
                    vy=random.uniform(-0.5, 0.5),
                    life=random.uniform(50.0, 110.0),
                    radius=random.uniform(1.4, 2.6)
                ))

            elif roll < 0.88:
                # Negative-contrast micro-droplet (swirls into violet Rayleigh streaming whirlpools)
                particles.append(Microbead(
                    px, py,
                    ptype="negative",
                    vx=random.uniform(-0.8, 0.8),
                    vy=random.uniform(-0.8, 0.8),
                    life=random.uniform(45.0, 95.0),
                    radius=random.uniform(1.6, 2.8)
                ))

            else:
                # Transducer acoustic cavitation spark at pressure antinodes
                particles.append(Microbead(
                    px, py,
                    ptype="spark",
                    vx=random.uniform(-2.5, 2.5),
                    vy=random.uniform(-2.5, 2.5),
                    life=random.uniform(20.0, 45.0),
                    radius=random.uniform(2.0, 4.0)
                ))

    # Update and Draw Lagrangian Particles with Additive Blending
    py5.blend_mode(py5.ADD)
    active_particles = []
    for p in particles:
        # Sample local forces from simulation coordinates
        sim_px = x_coords[0] + (p.x / py5.width) * (x_coords[-1] - x_coords[0])
        sim_py = y_coords[-1] - (p.y / py5.height) * (y_coords[-1] - y_coords[0])

        fx_rad = -np.sin(2.0 * kx_eff * sim_px) * np.cos(ky_eff * sim_py)**2
        fy_rad = -np.sin(2.0 * ky_eff * sim_py) * np.cos(kx_eff * sim_px)**2
        us_flow = -2.0 * ky_eff * np.sin(2.0 * kx_eff * sim_px) * np.cos(2.0 * ky_eff * sim_py)
        vs_flow = 2.0 * kx_eff * np.cos(2.0 * kx_eff * sim_px) * np.sin(2.0 * ky_eff * sim_py)

        p.update(fx_rad, fy_rad, us_flow, vs_flow)
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
        print(f"[Render Progress] Frame {frame}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Particles: {len(particles)}")

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

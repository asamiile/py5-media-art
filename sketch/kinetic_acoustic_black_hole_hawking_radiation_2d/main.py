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
Nx, Ny = 800, 450
x_coords = np.linspace(-4.0, 4.0, Nx, dtype=np.float32)
y_coords = np.linspace(-2.25, 2.25, Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)
dx = float(x_coords[1] - x_coords[0])
dy = float(y_coords[1] - y_coords[0])

# Physical Parameters of the Transonic Acoustic Black Hole
SOUND_SPEED = 1.0  # Normalized local speed of sound c_s = 1.0

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Dual Light Vectors for Specular Fluid Chrome Shading
light1 = np.array([0.55, -0.60, 0.58], dtype=np.float32)
light1 /= np.linalg.norm(light1)
light2 = np.array([-0.50, 0.55, 0.67], dtype=np.float32)
light2 /= np.linalg.norm(light2)
view_vec = np.array([0.0, 0.0, 1.0], dtype=np.float32)
h1 = (light1 + view_vec) / np.linalg.norm(light1 + view_vec)
h2 = (light2 + view_vec) / np.linalg.norm(light2 + view_vec)

# Lagrangian Particles: Entangled Hawking Phonons, Infalling Partners & Streamline Tracers
MAX_PARTICLES = 1600
particles = []


class PhononParticle:
    def __init__(self, px, py, ptype="hawking", vx=0.0, vy=0.0, life=120.0, radius=2.0):
        self.px = px
        self.py = py
        self.prev_x = px
        self.prev_y = py
        self.ptype = ptype  # "hawking", "partner", "streamline"
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.radius = radius

    def update(self, dt=1.0):
        self.prev_x = self.px
        self.prev_y = self.py

        if self.ptype == "hawking":
            # Escaping upstream against the transonic flow (-x direction)
            self.px += self.vx * dt
            self.py += (self.vy + random.uniform(-0.3, 0.3)) * dt
            self.vx *= 0.992
        elif self.ptype == "partner":
            # Swept downstream into supersonic drain (+x direction)
            self.px += self.vx * dt
            self.py += (self.vy + random.uniform(-0.4, 0.4)) * dt
            self.vx *= 1.01  # Accelerating downstream
        elif self.ptype == "streamline":
            # Laval nozzle fluid parcel
            self.px += self.vx * dt
            self.py += self.vy * dt
            self.vx *= 0.99

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


def compute_acoustic_horizon_fields(frame):
    """
    Computes 2D analogue gravity acoustic black hole fields:
    - Transonic de Laval nozzle flow profile with moving acoustic horizon X_H(t)
    - Entangled Hawking phonon wavepackets radiating upstream
    - Infalling partner wavepacket shearing into the supersonic drain
    - Supersonic cavitation vortices and Mach shock dissipation
    - 3D Blinn-Phong specular fluid normal shading
    """
    t = frame * 0.035
    t_norm = frame / TOTAL_FRAMES

    # 1. Acoustic Horizon Position & Breathing Modulation
    # Sonic horizon moves dynamically near x = 0
    X_H = 0.15 * np.sin(t * 1.8)
    
    # Distance from the sonic horizon (X_rel < 0 is subsonic upstream, X_rel > 0 is supersonic downstream)
    X_rel = X_grid - X_H

    # Flow velocity: subsonic (v ~ 0.5 c_s) upstream, supersonic (v ~ 1.8 c_s) downstream
    # Sonic horizon is exactly where v = SOUND_SPEED (1.0)
    v_flow = SOUND_SPEED * (1.0 + np.tanh(X_rel * 1.4) * 0.75)

    # 2. De Laval Nozzle Channel Geometry
    # Nozzle waist is narrowest near the horizon
    nozzle_half_width = 1.35 + 0.32 * (X_rel**2) * 0.15
    channel_envelope = 1.0 / (1.0 + np.exp((np.abs(Y_grid) - nozzle_half_width) * 8.0))

    # 3. Analogue Hawking Radiation (Escaping Upstream Phonons)
    # Originates at horizon and propagates UPSTREAM (into X_rel < 0)
    # High-frequency Bogoliubov dispersion wave train
    k_hawking = 20.0
    omega_hawking = 5.5
    upstream_mask = 1.0 / (1.0 + np.exp(X_rel * 8.0))  # Smooth step: 1 for X_rel < 0, 0 for X_rel > 0
    hawking_wave = (
        np.cos(k_hawking * X_rel + omega_hawking * t)
        * np.exp(X_rel * 0.9)  # Decays smoothly as it moves upstream away from horizon
        * upstream_mask
        * channel_envelope
        * np.exp(- (Y_grid**2) / 0.85)
    )

    # 4. Infalling Negative-Energy Partner Wave (Downstream Supersonic Infall)
    # Swept downstream into X_rel > 0 with strong spatial stretching (Doppler redshift)
    k_infall = 11.0
    downstream_mask = 1.0 / (1.0 + np.exp(-X_rel * 8.0))  # Smooth step: 1 for X_rel > 0
    infalling_wave = (
        np.cos(k_infall * X_rel - omega_hawking * t * 1.3)
        * np.exp(-X_rel * 0.7)  # Shears downstream
        * downstream_mask
        * channel_envelope
        * np.exp(- (Y_grid**2) / 0.95)
    )

    # 5. Sonic Event Horizon Shear Line (Razor-sharp localized acoustic boundary)
    horizon_sheet = (
        np.exp(- (X_rel / 0.08)**2)
        * (1.0 + 0.35 * np.cos(Y_grid * 8.0 - t * 3.0))
        * channel_envelope
        * 2.8
    )

    # 6. Supersonic Cavitation Vortices (Downstream Turbulent Eddies)
    eddy_x = X_rel - 1.2
    eddy_phase = t * 2.2
    cavitation_vortices = (
        (np.cos(eddy_x * 4.5 + Y_grid * 4.0 - eddy_phase)**2)
        * downstream_mask
        * np.exp(- (eddy_x / 1.4)**2)
        * channel_envelope
        * 0.75
    )

    # 7. Total Acoustic Fluid Energy Density
    I_fluid = (
        horizon_sheet * 1.4
        + hawking_wave * 1.1
        + infalling_wave * 0.95
        + cavitation_vortices * 0.65
        + channel_envelope * 0.55
    )

    # 8. 3D Blinn-Phong Specular Fluid Normal Shading
    H_surf = np.sqrt(np.clip(I_fluid, 0.0, 4.0)) * 0.58
    grad_H_y, grad_H_x = np.gradient(H_surf, dy, dx)
    norm_denom = np.sqrt(grad_H_x**2 + grad_H_y**2 + 1.0)
    Nx_s = -grad_H_x / norm_denom
    Ny_s = -grad_H_y / norm_denom
    Nz_s = 1.0 / norm_denom

    # Light 1: Cool azure specular reflection
    spec1 = np.maximum(0.0, Nx_s * h1[0] + Ny_s * h1[1] + Nz_s * h1[2])**22
    # Light 2: Radiant actinic violet specular reflection
    spec2 = np.maximum(0.0, Nx_s * h2[0] + Ny_s * h2[1] + Nz_s * h2[2])**16

    return (
        I_fluid,
        horizon_sheet,
        hawking_wave,
        infalling_wave,
        cavitation_vortices,
        spec1,
        spec2,
        X_H,
        t,
    )


def render_acoustic_canvas(
    I_fluid,
    horizon_sheet,
    hawking_wave,
    infalling_wave,
    cavitation_vortices,
    spec1,
    spec2,
):
    """
    Renders 4-channel image into pixel_buffer following 60-30-10 palette rules:
    - 60% Subsonic Vacuum Obsidian Void & Deep Quantum Indigo (#02030a, #060919)
    - 30% Transonic Fluid Streamlines & Entangled Phonon Azure (#0ea5e9, #38bdf8, #0284c7)
    - 30% Secondary: Supersonic Horizon Shear & Actinic Violet Cavitation (#8b5cf6, #7c3aed, #4c1d95)
    - 10% Accent: Incandescent Sonic Horizon Singularity Diamond-White & Solar Gold (#ffffff, #fde047)
    """
    # 1. Background 60%: Cryogenic sub-channel obsidian void
    r_bg = 2.0 + np.exp(- (X_grid**2 + Y_grid**2) / 8.0) * 3.0
    g_bg = 3.0 + np.exp(- (X_grid**2 + Y_grid**2) / 8.0) * 6.0
    b_bg = 10.0 + np.exp(- (X_grid**2 + Y_grid**2) / 8.0) * 22.0

    # 2. Dominant 60% (of foreground): Transonic Fluid & Entangled Phonon Azure (#0ea5e9, #38bdf8)
    azure_stream = np.clip(hawking_wave * 1.45 + np.maximum(0.0, I_fluid * 0.5), 0.0, 2.5)
    r_azure = azure_stream * 14.0
    g_azure = azure_stream * 165.0
    b_azure = azure_stream * 233.0

    # Secondary 30%: Supersonic Horizon Shear & Actinic Violet Cavitation (#8b5cf6, #7c3aed)
    violet_stream = np.clip(infalling_wave * 1.35 + cavitation_vortices * 1.2, 0.0, 2.5)
    r_violet = violet_stream * 139.0
    g_violet = violet_stream * 92.0
    b_violet = violet_stream * 246.0

    # Specular liquid chrome highlights (Light 1: ice-azure, Light 2: violet-gold)
    spec_r = spec1 * 120.0 + spec2 * 230.0
    spec_g = spec1 * 225.0 + spec2 * 170.0
    spec_b = spec1 * 255.0 + spec2 * 255.0

    # Combined transonic fluid foreground
    r_wave = r_azure * 0.65 + r_violet * 0.35 + spec_r * 0.40
    g_wave = g_azure * 0.70 + g_violet * 0.30 + spec_g * 0.40
    b_wave = b_azure * 0.55 + b_violet * 0.45 + spec_b * 0.40

    blend_factor = np.clip(I_fluid * 0.85, 0.0, 1.0)
    r_mid = r_bg * (1.0 - blend_factor) + r_wave * blend_factor
    g_mid = g_bg * (1.0 - blend_factor) + g_wave * blend_factor
    b_mid = b_bg * (1.0 - blend_factor) + b_wave * blend_factor

    # 3. Accent 10%: Incandescent Sonic Horizon Singularity Diamond-White & Solar Gold (#ffffff, #fde047)
    horizon_accent = np.clip((horizon_sheet * horizon_sheet) * 1.8 + spec1 * 0.50, 0.0, 2.8)
    r_accent = horizon_accent * 255.0
    g_accent = horizon_accent * 245.0
    b_accent = horizon_accent * 180.0

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

    # 1. Compute acoustic black hole fields
    (
        I_fluid,
        horizon_sheet,
        hawking_wave,
        infalling_wave,
        cavitation_vortices,
        spec1,
        spec2,
        X_H,
        t,
    ) = compute_acoustic_horizon_fields(py5.frame_count)

    # 2. Render pixel buffer canvas
    render_acoustic_canvas(
        I_fluid,
        horizon_sheet,
        hawking_wave,
        infalling_wave,
        cavitation_vortices,
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

    # 4. Map horizon location to screen space
    screen_horizon_x = (X_H - x_coords[0]) / (x_coords[-1] - x_coords[0]) * py5.width

    # 5. Spawn Lagrangian Quantum Phonons & Entangled Pairs
    if len(particles) < MAX_PARTICLES:
        spawn_n = min(45, MAX_PARTICLES - len(particles))
        for _ in range(spawn_n):
            roll = random.random()

            if roll < 0.50:
                # Entangled Hawking Phonon: Escaping upstream (to the left, -x)
                spawn_y = py5.height * 0.5 + random.gauss(0.0, 160.0)
                speed_esc = -random.uniform(2.5, 6.5)  # Directed upstream
                particles.append(PhononParticle(
                    screen_horizon_x - random.uniform(2.0, 15.0),
                    spawn_y,
                    ptype="hawking",
                    vx=speed_esc,
                    vy=random.uniform(-0.8, 0.8),
                    life=random.uniform(60.0, 120.0),
                    radius=random.uniform(1.4, 2.8)
                ))

            elif roll < 0.80:
                # Infalling Partner Phonon: Swept downstream into supersonic drain (to the right, +x)
                spawn_y = py5.height * 0.5 + random.gauss(0.0, 160.0)
                speed_inf = random.uniform(4.0, 9.5)  # Accelerated downstream
                particles.append(PhononParticle(
                    screen_horizon_x + random.uniform(2.0, 15.0),
                    spawn_y,
                    ptype="partner",
                    vx=speed_inf,
                    vy=random.uniform(-1.2, 1.2),
                    life=random.uniform(40.0, 85.0),
                    radius=random.uniform(1.8, 3.2)
                ))

            else:
                # Streamline Tracers: Fluid advecting through the nozzle
                spawn_x = random.uniform(-50.0, screen_horizon_x)
                spawn_y = py5.height * 0.5 + random.gauss(0.0, 200.0)
                particles.append(PhononParticle(
                    spawn_x,
                    spawn_y,
                    ptype="streamline",
                    vx=random.uniform(1.5, 4.0),
                    vy=random.uniform(-0.5, 0.5),
                    life=random.uniform(80.0, 150.0),
                    radius=random.uniform(1.2, 2.2)
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

            if p.ptype == "hawking":
                # Escaping Hawking radiation: Electric azure & pure white (#38bdf8, #ffffff)
                py5.no_stroke()
                py5.fill(14, 165, 233, int(alpha * 0.40))
                py5.circle(p.px, p.py, p.radius * 3.4)
                py5.fill(235, 248, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 0.95)
                py5.stroke(56, 189, 248, int(alpha * 0.75))
                py5.stroke_weight(1.3)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            elif p.ptype == "partner":
                # Infalling partner: Actinic violet & royal magenta (#8b5cf6, #c084fc)
                py5.no_stroke()
                py5.fill(139, 92, 246, int(alpha * 0.42))
                py5.circle(p.px, p.py, p.radius * 3.2)
                py5.fill(240, 220, 255, alpha)
                py5.circle(p.px, p.py, p.radius * 1.0)
                py5.stroke(168, 85, 247, int(alpha * 0.80))
                py5.stroke_weight(1.6)
                py5.line(p.px, p.py, p.prev_x, p.prev_y)

            elif p.ptype == "streamline":
                # Streamline tracer: Glacial cyan (#0284c7)
                py5.no_stroke()
                py5.fill(2, 132, 199, int(alpha * 0.28))
                py5.circle(p.px, p.py, p.radius * 2.6)
                py5.fill(186, 230, 253, alpha)
                py5.circle(p.px, p.py, p.radius * 0.8)

    particles = active_particles

    # 7. Render Sonic Horizon Singularity Vertical Line (Incandescent White-Gold)
    py5.no_stroke()
    # Broad aura
    py5.fill(14, 165, 233, 40)
    py5.rect(screen_horizon_x - 30.0, 0, 60.0, py5.height)
    # Intermediate violet shear
    py5.fill(139, 92, 246, 80)
    py5.rect(screen_horizon_x - 12.0, 0, 24.0, py5.height)
    # Incandescent white core line
    py5.fill(255, 255, 255, 210)
    py5.rect(screen_horizon_x - 3.0, 0, 6.0, py5.height)
    # Gold focal nodes
    for y_knot in [0.25, 0.5, 0.75]:
        py5.fill(253, 224, 71, 190)
        py5.circle(screen_horizon_x, py5.height * y_knot, 16.0)

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
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Phonons: {len(particles)}")

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

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
DURATION_SEC = 18
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Spatial Simulation Grid (16:9 aspect ratio)
Nx, Ny = 640, 360
x_coords = np.linspace(-6.0, 6.0, Nx, dtype=np.float32)
y_coords = np.linspace(-6.0 * (Ny / Nx), 6.0 * (Ny / Nx), Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# 5 Belousov-Zhabotinsky Chemical Spiral Wave Rotors
# (cx0, cy0, r_meander, m_meander, chirality, m_rot, k)
ROTOR_SPECS = [
    (-2.6, -1.1, 0.22, 1, 1.0, 6, 2.4),
    (2.7, 1.0, 0.25, -1, 1.0, 6, 2.4),
    (-0.6, 1.4, 0.18, 2, -1.0, 5, 2.2),
    (0.9, -1.5, 0.20, -2, -1.0, 5, 2.2),
    (0.1, 0.05, 0.15, 1, 1.0, 6, 2.5),
]

# Catalytic Indicator Tracer Particles
MAX_PARTICLES = 850
tracer_particles = []


class CatalyticSpark:
    def __init__(self, px, py):
        self.px = px
        self.py = py
        self.vx = 0.0
        self.vy = 0.0
        self.prev_x = self.px
        self.prev_y = self.py
        self.life = random.uniform(50.0, 160.0)
        self.max_life = self.life
        self.size = random.uniform(1.8, 3.6)

    def update(self, grad_x, grad_y, local_front):
        self.prev_x = self.px
        self.prev_y = self.py

        # Advection along reaction wavefront normal + gentle lateral drift
        speed = 2.4 + local_front * 4.8
        drift_x = -grad_y * 0.4 + random.uniform(-0.3, 0.3)
        drift_y = grad_x * 0.4 + random.uniform(-0.3, 0.3)

        self.vx = self.vx * 0.82 + (grad_x * speed + drift_x) * 0.28
        self.vy = self.vy * 0.82 + (grad_y * speed + drift_y) * 0.28

        self.px += self.vx
        self.py += self.vy

        # Out-of-bounds check
        if self.px < 0 or self.px >= py5.width or self.py < 0 or self.py >= py5.height:
            self.life = 0

        self.life -= 1.0

    @property
    def is_dead(self):
        return self.life <= 0


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def compute_bz_reaction(frame_idx):
    # Normalized loop time tau in [0, 2*pi] over TOTAL_FRAMES
    tau = (2.0 * np.pi * frame_idx) / TOTAL_FRAMES

    # Complex chemical activator field Z(x, y) = U + i V
    Z = np.zeros((Ny, Nx), dtype=np.complex64)
    core_spikes = np.zeros_like(X_grid)

    for cx0, cy0, r_m, m_m, chirality, m_rot, k in ROTOR_SPECS:
        # Meandering rotor center
        cx = cx0 + r_m * np.cos(m_m * tau)
        cy = cy0 + r_m * np.sin(m_m * tau)

        dx = X_grid - cx
        dy = Y_grid - cy
        r = np.sqrt(dx**2 + dy**2) + 1e-4
        theta = np.arctan2(dy, dx)

        # Archimedean spiral phase: phi = chirality * theta - k * r + m_rot * tau
        phi = chirality * theta - k * r + m_rot * tau
        amp = np.tanh(r / 0.52) * np.exp(- (r / 6.6)**2)
        Z += amp * np.exp(1j * phi)

        # Rotor singularity core glow
        d_core = np.sqrt(dx**2 + dy**2)
        core_spikes += np.exp(- (d_core / 0.18)**2)

    # Chemical activator and inhibitor concentrations
    u_raw = np.real(Z)
    v_raw = np.imag(Z)
    u_chem = np.tanh(1.8 * u_raw)
    v_chem = np.tanh(1.8 * v_raw)

    # Sharp catalytic reaction fronts (Oregonator excitable threshold)
    front_oxidized = np.exp(- ((u_chem - 0.75) / 0.14)**2)
    secondary_front = np.exp(- ((v_chem - 0.70) / 0.16)**2)
    refractory_wake = np.exp(- ((u_chem + 0.5) / 0.28)**2)

    # Gradient of oxidized front for particle advection
    du_dx = np.gradient(front_oxidized, axis=1)
    du_dy = np.gradient(front_oxidized, axis=0)

    return Z, u_chem, v_chem, front_oxidized, secondary_front, refractory_wake, core_spikes, du_dx, du_dy


def render_bz_field(Z, u_chem, v_chem, front_oxidized, secondary_front, refractory_wake, core_spikes):
    # Palette Architecture:
    # 1. 60% Matrix: Reduced Catalyst Ferroin / Deep Maroon-Obsidian (#030107)
    r = np.full_like(X_grid, 3.0)
    g = np.full_like(X_grid, 1.0)
    b = np.full_like(X_grid, 7.0)

    # Ambient chemical state wave energy (Royal Amethyst & Deep Indigo)
    act = np.clip(np.abs(Z) / 1.85, 0.0, 1.0)
    r += act * 26.0 + (u_chem * 0.5 + 0.5) * 22.0
    g += act * 6.0 + (v_chem * 0.5 + 0.5) * 14.0
    b += act * 98.0 + (u_chem * 0.5 + 0.5) * 48.0

    # Refractory wave wake (Deep Indigo / Violet Sheen)
    r += refractory_wake * 42.0
    g += refractory_wake * 12.0
    b += refractory_wake * 92.0

    # 2. 30% Primary Oxidized Fronts: Luminescent Ferriin Electric Cyan & Jade Emerald
    r += front_oxidized * 10.0
    g += front_oxidized * 248.0
    b += front_oxidized * 225.0

    # Secondary excitation wave: Neon Violet / Magenta
    r += secondary_front * 168.0
    g += secondary_front * 36.0
    b += secondary_front * 232.0

    # 3. 10% Rotor Singularities & Annihilation Peaks: Solar Amber & Pure White
    r += core_spikes * 255.0
    g += core_spikes * 235.0
    b += core_spikes * 140.0

    peak_front = front_oxidized**2.5
    r += peak_front * 255.0
    g += peak_front * 255.0
    b += peak_front * 240.0

    # Assemble into py5 ARGB buffer
    pixel_buffer[..., 0] = 255
    pixel_buffer[..., 1] = np.clip(r, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b, 0, 255).astype(np.uint8)


def draw_frame():
    global tracer_particles

    # 1. Physics update
    (Z, u_chem, v_chem, front_oxidized,
     secondary_front, refractory_wake,
     core_spikes, du_dx, du_dy) = compute_bz_reaction(py5.frame_count)

    # 2. Render field into pixel buffer
    render_bz_field(Z, u_chem, v_chem, front_oxidized, secondary_front, refractory_wake, core_spikes)

    # 3. Blit upscaled to 4K canvas
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

    # 4. Spawn catalytic spark tracers
    if len(tracer_particles) < MAX_PARTICLES:
        spawn_n = min(30, MAX_PARTICLES - len(tracer_particles))
        for _ in range(spawn_n):
            spx = random.uniform(0, py5.width)
            spy = random.uniform(0, py5.height)
            tracer_particles.append(CatalyticSpark(spx, spy))

    # 5. Render catalytic spark tracers with ADD blend mode
    py5.blend_mode(py5.ADD)
    active_particles = []
    for p in tracer_particles:
        gx = int(np.clip((p.px / py5.width) * (Nx - 1), 0, Nx - 1))
        gy = int(np.clip((p.py / py5.height) * (Ny - 1), 0, Ny - 1))

        local_grad_x = du_dx[gy, gx]
        local_grad_y = du_dy[gy, gx]
        local_front = front_oxidized[gy, gx]

        p.update(local_grad_x, local_grad_y, local_front)

        if not p.is_dead:
            active_particles.append(p)
            life_norm = p.life / p.max_life
            alpha = int(life_norm * (160 + local_front * 90))

            # Color shifts from Electric Cyan to Amber when near reaction front
            if local_front > 0.4:
                cr = int(245)
                cg = int(220 + life_norm * 30)
                cb = int(140 + life_norm * 60)
            else:
                cr = int(80 + life_norm * 60)
                cg = int(240 + life_norm * 15)
                cb = int(225 + life_norm * 30)

            # Spark aura
            py5.no_stroke()
            py5.fill(cr, cg, cb, int(alpha * 0.4))
            py5.circle(p.px, p.py, p.size * 2.8)

            # Spark nucleus
            py5.fill(255, 255, 245, alpha)
            py5.circle(p.px, p.py, p.size * 1.1)

            # Trail filament
            py5.stroke(cr, cg, cb, int(alpha * 0.5))
            py5.stroke_weight(1.3)
            py5.line(p.px, p.py, p.prev_x, p.prev_y)

    tracer_particles = active_particles
    py5.blend_mode(py5.BLEND)

    # Fail-safe blank screen check
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Save animation frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        progress_pct = (py5.frame_count / TOTAL_FRAMES) * 100.0
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Active Tracers: {len(tracer_particles)}")

    # Finalize render
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


py5.run_sketch()

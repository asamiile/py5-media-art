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

# Simulation Grid (16:9 aspect ratio)
Nx, Ny = 640, 360
x = np.linspace(-1, 1, Nx, dtype=np.float32)
y = np.linspace(-1, 1, Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x, y)

# Multi-scale quenched disorder pinning field (micro-defect landscape)
pinning = np.zeros((Ny, Nx), dtype=np.float32)
num_defects = 280
for _ in range(num_defects):
    cx = random.uniform(-1.0, 1.0)
    cy = random.uniform(-1.0, 1.0)
    rad = random.uniform(0.008, 0.055)
    amp = random.uniform(0.35, 0.95) * random.choice([-1.0, 1.0])
    pinning += amp * np.exp(- ((X_grid - cx)**2 + (Y_grid - cy)**2) / (2.0 * rad**2))

# Polycrystalline grain orientations (anisotropic texture and grain boundaries)
num_grains = 38
grain_seeds_x = np.array([random.uniform(-1.0, 1.0) for _ in range(num_grains)], dtype=np.float32)
grain_seeds_y = np.array([random.uniform(-1.0, 1.0) for _ in range(num_grains)], dtype=np.float32)
grain_angles = np.array([random.uniform(0.0, np.pi) for _ in range(num_grains)], dtype=np.float32)

grain_dists = (X_grid[:, :, None] - grain_seeds_x[None, None, :])**2 + (Y_grid[:, :, None] - grain_seeds_y[None, None, :])**2
nearest_grain = np.argmin(grain_dists, axis=2)
grain_anisotropy = grain_angles[nearest_grain]
grain_edge = (nearest_grain != np.roll(nearest_grain, 1, axis=0)) | (nearest_grain != np.roll(nearest_grain, 1, axis=1))

# Micro-crystallographic striations
micro_striations = np.sin((X_grid * np.cos(grain_anisotropy) + Y_grid * np.sin(grain_anisotropy)) * 85.0) * 0.05

# Ferromagnetic domain magnetization order parameter m in [-1, 1]
phase_x = random.uniform(2.8, 3.8)
phase_y = random.uniform(2.2, 3.2)
m = np.tanh(pinning * 1.9 + np.sin(phase_x * np.pi * X_grid + np.cos(phase_y * np.pi * Y_grid)) * 1.25).astype(np.float32)

# Acoustic emission ripple radiation field
acoustic_field = np.zeros((Ny, Nx), dtype=np.float32)
dt = 0.045

# RGBA pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Barkhausen Acoustic Emission Sparks (high-energy radiation pulses)
MAX_SPARKS = 350
sparks = []


class BarkhausenSpark:
    def __init__(self, px, py, nx, ny, intensity):
        self.px = px
        self.py = py
        speed = random.uniform(2.5, 7.5) * (1.0 + intensity * 0.8)
        angle = np.arctan2(ny, nx) + random.uniform(-0.8, 0.8)
        self.vx = np.cos(angle) * speed
        self.vy = np.sin(angle) * speed
        self.life = random.uniform(12.0, 32.0)
        self.max_life = self.life
        self.size = random.uniform(1.8, 4.2)
        self.intensity = intensity

    def update(self):
        self.px += self.vx
        self.py += self.vy
        self.vx *= 0.93
        self.vy *= 0.93
        self.life -= 1.0

    @property
    def is_dead(self):
        return (self.life <= 0 or self.px < -30 or self.px > py5.width + 30 or
                self.py < -30 or self.py > py5.height + 30)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def update_barkhausen_physics(frame_idx):
    global m, acoustic_field, sparks

    # Alternating external magnetic field driving cyclic hysteresis depinning
    # Cycle period ~ 360 frames (3 full hysteresis loops across 1080 frames)
    t_phase = (frame_idx / TOTAL_FRAMES) * 6.0 * np.pi
    H_ext = 0.46 * np.sin(t_phase)

    # 1. Domain wall surface tension via 2D discrete Laplacian
    lap_m = (np.roll(m, 1, axis=1) + np.roll(m, -1, axis=1) +
             np.roll(m, 1, axis=0) + np.roll(m, -1, axis=0) - 4.0 * m)

    # 2. Non-local demagnetizing / dipolar interaction stabilizing multi-domain stripe morphology
    demag_field = - 0.24 * np.mean(m)

    # 3. Allen-Cahn equation with quenched disorder pinning
    dm = 0.62 * lap_m + (m - m**3) + H_ext + 0.52 * pinning + demag_field
    m_new = np.clip(m + dt * dm, -1.0, 1.0)

    # 4. Avalanche rate: instantaneous velocity of domain wall depinning
    avalanche = np.abs(m_new - m) / dt
    m = m_new

    # 5. Acoustic emission wave propagation (diffusive radiation of acoustic shock pulses)
    lap_ac = (np.roll(acoustic_field, 1, axis=1) + np.roll(acoustic_field, -1, axis=1) +
              np.roll(acoustic_field, 1, axis=0) + np.roll(acoustic_field, -1, axis=0) - 4.0 * acoustic_field)
    acoustic_field = np.clip(
        acoustic_field * 0.87 + 0.13 * lap_ac + np.clip((avalanche - 0.08) * 2.4, 0.0, 3.5),
        0.0, 4.0
    )

    # 6. Domain boundary wall normal vector
    gm_x = (np.roll(m, -1, axis=1) - np.roll(m, 1, axis=1)) * 0.5
    gm_y = (np.roll(m, -1, axis=0) - np.roll(m, 1, axis=0)) * 0.5
    wall_mag = np.sqrt(gm_x**2 + gm_y**2)

    # Spawn acoustic emission sparks at high-avalanche unpinning events
    if len(sparks) < MAX_SPARKS:
        high_aval = np.argwhere(avalanche > 0.32)
        if len(high_aval) > 0:
            spawn_count = min(18, MAX_SPARKS - len(sparks))
            picks = np.random.choice(len(high_aval), size=spawn_count, replace=True)
            for pick in picks:
                gy, gx = high_aval[pick]
                spx = (gx / Nx) * py5.width + random.uniform(-3.0, 3.0)
                spy = (gy / Ny) * py5.height + random.uniform(-3.0, 3.0)
                nx_val = gm_x[gy, gx]
                ny_val = gm_y[gy, gx]
                w_norm = max(1e-4, wall_mag[gy, gx])
                intensity = float(avalanche[gy, gx])
                sparks.append(BarkhausenSpark(spx, spy, nx_val / w_norm, ny_val / w_norm, intensity))

    return avalanche, wall_mag


def render_barkhausen_field(avalanche, wall_mag):
    global pixel_buffer

    # 1. Base Polycrystalline Obsidian Matrix (60% background/matrix): #050811
    r = np.full_like(m, 4.0)
    g = np.full_like(m, 8.0)
    b = np.full_like(m, 17.0)

    # Crystalline micro-striations
    r += micro_striations * 22.0
    g += micro_striations * 32.0
    b += micro_striations * 56.0

    # Up-spin domain (m > 0): Midnight Royal Cobalt Sheen
    up = np.clip(m, 0.0, 1.0)
    r += up * 24.0
    g += up * 20.0
    b += up * 58.0

    # Down-spin domain (m < 0): Slate Steel Matrix
    down = np.clip(-m, 0.0, 1.0)
    r += down * 10.0
    g += down * 24.0
    b += down * 46.0

    # Crystal grain boundary facets
    r[grain_edge] += 16.0
    g[grain_edge] += 30.0
    b[grain_edge] += 54.0

    # 2. Acoustic Radiation Ripples (Shock waves from depinning avalanches)
    ac_norm = np.clip(acoustic_field / 1.6, 0.0, 1.0)
    r += ac_norm * 22.0
    g += ac_norm * 88.0
    b += ac_norm * 148.0

    # 3. Domain Boundary Walls (30% secondary): Electric Turquoise & Cyan Glow
    wall = np.clip(wall_mag * 2.8, 0.0, 1.0)
    r += wall * 18.0
    g += wall * 215.0
    b += wall * 192.0

    # Intense wall core
    wall_core = np.clip((wall - 0.62) / 0.38, 0.0, 1.0)**2.0
    r += wall_core * 110.0
    g += wall_core * 245.0
    b += wall_core * 238.0

    # 4. Barkhausen Avalanche Bursts (10% accent): Solar Amber to Incandescent White
    burst = np.clip((avalanche - 0.10) / 0.35, 0.0, 1.0)**1.2
    r += burst * 255.0
    g += burst * 205.0
    b += burst * 45.0

    # Peak unpinning core: Pure incandescent diamond-white
    peak_burst = np.clip((avalanche - 0.36) / 0.32, 0.0, 1.0)**1.5
    r += peak_burst * 255.0
    g += peak_burst * 255.0
    b += peak_burst * 240.0

    # Assemble into py5 ARGB buffer (0=Alpha, 1=Red, 2=Green, 3=Blue)
    pixel_buffer[..., 0] = 255
    pixel_buffer[..., 1] = np.clip(r, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b, 0, 255).astype(np.uint8)


def draw_frame():
    global sparks

    # 1. Physics update
    avalanche, wall_mag = update_barkhausen_physics(py5.frame_count)

    # 2. Render field into pixel buffer
    render_barkhausen_field(avalanche, wall_mag)

    # 3. Blit field image upscaled to 4K
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

    # 4. Render Barkhausen Acoustic Sparks on 4K Canvas
    py5.blend_mode(py5.ADD)
    active_sparks = []
    for s in sparks:
        s.update()
        if not s.is_dead:
            active_sparks.append(s)
            life_ratio = s.life / s.max_life
            alpha = int(life_ratio * 240)

            # Spark color transitions from incandescent solar gold to ember red
            sr = 255
            sg = int(180 + life_ratio * 65)
            sb = int(40 + life_ratio * 180)

            # Outer glow halo
            py5.no_stroke()
            py5.fill(sr, sg, sb, int(alpha * 0.35))
            py5.circle(s.px, s.py, s.size * 2.8)

            # Brilliant core
            py5.fill(sr, sg, sb, alpha)
            py5.circle(s.px, s.py, s.size * 1.1)

            # Radiation trail
            py5.stroke(sr, sg, sb, int(alpha * 0.45))
            py5.stroke_weight(1.2)
            py5.line(s.px, s.py, s.px - s.vx * 2.2, s.py - s.vy * 2.2)

    sparks = active_sparks
    py5.blend_mode(py5.BLEND)

    # Fail-safe check
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
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({progress_pct:.1f}%) | Active Sparks: {len(sparks)}")

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

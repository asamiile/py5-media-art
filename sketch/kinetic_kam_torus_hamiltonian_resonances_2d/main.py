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
x_coords = np.linspace(-4.6, 4.6, Nx, dtype=np.float32)
y_coords = np.linspace(-4.6 * (Ny / Nx), 4.6 * (Ny / Nx), Ny, dtype=np.float32)
X_grid, Y_grid = np.meshgrid(x_coords, y_coords)

R2_grid = X_grid**2 + Y_grid**2
R_grid = np.sqrt(R2_grid) + 1e-5
Theta_grid = np.arctan2(Y_grid, X_grid)

# Pixel buffer for py5 ARGB format (0=Alpha, 1=Red, 2=Green, 3=Blue)
pixel_buffer = np.zeros((Ny, Nx, 4), dtype=np.uint8)
pixel_buffer[..., 0] = 255

# Symplectic Phase-Space Tracer Particles
MAX_PARTICLES = 850
tracer_particles = []


class SymplecticSpark:
    def __init__(self, px, py):
        self.px = px
        self.py = py
        self.vx = 0.0
        self.vy = 0.0
        self.prev_x = self.px
        self.prev_y = self.py
        self.life = random.uniform(60.0, 180.0)
        self.max_life = self.life
        self.size = random.uniform(1.8, 3.6)

    def update(self, vx_flow, vy_flow, local_tori):
        self.prev_x = self.px
        self.prev_y = self.py

        # Symplectic flow speed with micro-jitter
        speed_boost = 4.2 + local_tori * 2.8
        jx = random.uniform(-0.15, 0.15)
        jy = random.uniform(-0.15, 0.15)

        self.vx = self.vx * 0.84 + (vx_flow * speed_boost + jx) * 0.22
        self.vy = self.vy * 0.84 + (vy_flow * speed_boost + jy) * 0.22

        self.px += self.vx
        self.py += self.vy

        # Out of bounds check
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


def compute_hamiltonian_phase_space(frame_idx):
    # Normalized loop time tau in [0, 2*pi] over TOTAL_FRAMES
    tau = (2.0 * np.pi * frame_idx) / TOTAL_FRAMES

    # Radial base potential with asymptotic soft saturation
    R_eff = 2.3 + 1.2 * np.tanh((R_grid - 2.3) / 1.2)
    H0 = 0.55 * (R_eff - 2.3)**2 + 0.05 * R2_grid * np.exp(- (R_grid / 3.6)**2)

    # Multi-order orbital resonances (Poincare-Birkhoff island chains)
    # Mode frequencies are integers to ensure perfect seamless 18.0s periodicity
    res3 = 0.22 * np.exp(- ((R_grid - 1.25) / 0.55)**2) * np.cos(3.0 * Theta_grid - 1.0 * tau)
    res5 = 0.32 * np.exp(- ((R_grid - 2.45) / 0.70)**2) * np.cos(5.0 * Theta_grid + 2.0 * tau)
    res7 = 0.20 * np.exp(- ((R_grid - 3.65) / 0.75)**2) * np.cos(7.0 * Theta_grid - 1.0 * tau)
    res2 = 0.12 * np.exp(- ((R_grid - 2.80) / 1.40)**2) * np.cos(2.0 * Theta_grid + 1.0 * tau)

    H = H0 + res3 + res5 + res7 + res2

    # Adaptive invariant KAM tori contour phase: dampens gracefully at margins
    k_tori = 20.0 * np.pi / (1.0 + (R_grid / 3.6)**2)
    tori_phase = k_tori * H
    tori_filaments = np.exp(- ((np.sin(tori_phase * 0.5)) / 0.20)**2)
    tori_fine = np.exp(- ((np.sin(tori_phase * 1.5)) / 0.16)**2) * 0.40

    # Smooth outer frame vignette
    vignette = np.exp(- (R_grid / 4.4)**6)

    # Symplectic gradient field: vx = dH/dy, vy = -dH/dx
    dH_dy = np.gradient(H, axis=0) * (Ny / (9.2 * (Ny / Nx)))
    dH_dx = np.gradient(H, axis=1) * (Nx / 9.2)

    force_mag = np.sqrt(dH_dx**2 + dH_dy**2)

    # Elliptic island cores: local extrema where |grad H| -> 0
    island_cores = np.exp(- (force_mag / 0.22)**2) * np.exp(- ((R_grid - 2.4) / 1.8)**2)
    center_core = np.exp(- (R_grid / 0.24)**2)

    # Separatrix shock lines (saddle points of H)
    separatrix = (np.exp(- ((H - 0.25) / 0.025)**2) + np.exp(- ((H - 0.55) / 0.035)**2)) * vignette

    return H, tori_filaments, tori_fine, separatrix, island_cores, center_core, vignette, dH_dy, -dH_dx


def render_phase_space(H, tori_filaments, tori_fine, separatrix, island_cores, center_core, vignette):
    # Palette Architecture:
    # 1. 60% Matrix: Deep Celestial Obsidian & Abyssal Indigo (#020309, #080618)
    r = np.full_like(X_grid, 2.0)
    g = np.full_like(X_grid, 3.0)
    b = np.full_like(X_grid, 9.0)

    # Ambient potential depth (Deep Indigo & Royal Purple)
    H_norm = np.clip((H - np.min(H)) / (np.max(H) - np.min(H) + 1e-4), 0.0, 1.0)
    r += H_norm * 32.0 * vignette
    g += H_norm * 14.0 * vignette
    b += H_norm * 115.0 * vignette

    # 2. 30% Invariant KAM Tori Filaments (Electric Cyan & Luminescent Jade)
    tori_total = (tori_filaments + tori_fine) * vignette
    r += tori_total * 10.0
    g += tori_total * 248.0
    b += tori_total * 222.0

    # Resonance separatrices (Neon Violet & Royal Magenta)
    r += separatrix * 195.0
    g += separatrix * 35.0
    b += separatrix * 235.0

    # 3. 10% Elliptic Island Cores & Singularities: Solar Amber & Diamond White
    r += island_cores * vignette * 255.0
    g += island_cores * vignette * 225.0
    b += island_cores * vignette * 135.0

    r += center_core * 255.0
    g += center_core * 250.0
    b += center_core * 210.0

    # Assemble into py5 ARGB buffer
    pixel_buffer[..., 0] = 255
    pixel_buffer[..., 1] = np.clip(r, 0, 255).astype(np.uint8)
    pixel_buffer[..., 2] = np.clip(g, 0, 255).astype(np.uint8)
    pixel_buffer[..., 3] = np.clip(b, 0, 255).astype(np.uint8)


def draw_frame():
    global tracer_particles

    # 1. Physics update
    (H, tori_filaments, tori_fine, separatrix,
     island_cores, center_core, vignette,
     vx_flow, vy_flow) = compute_hamiltonian_phase_space(py5.frame_count)

    # 2. Render field into pixel buffer
    render_phase_space(H, tori_filaments, tori_fine, separatrix, island_cores, center_core, vignette)

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

    # 4. Spawn symplectic tracer sparks
    center_px = py5.width / 2.0
    center_py = py5.height / 2.0
    if len(tracer_particles) < MAX_PARTICLES:
        spawn_n = min(25, MAX_PARTICLES - len(tracer_particles))
        for _ in range(spawn_n):
            angle = random.uniform(0.0, 2.0 * np.pi)
            rad = np.sqrt(random.uniform(0.08, 0.95)) * (py5.height * 0.46)
            spx = center_px + np.cos(angle) * rad * 1.5
            spy = center_py + np.sin(angle) * rad
            tracer_particles.append(SymplecticSpark(spx, spy))

    # 5. Render symplectic tracer sparks with ADD blend mode
    py5.blend_mode(py5.ADD)
    active_particles = []
    for p in tracer_particles:
        gx = int(np.clip((p.px / py5.width) * (Nx - 1), 0, Nx - 1))
        gy = int(np.clip((p.py / py5.height) * (Ny - 1), 0, Ny - 1))

        local_vx = vx_flow[gy, gx]
        local_vy = vy_flow[gy, gx]
        local_tori = tori_filaments[gy, gx]

        p.update(local_vx, local_vy, local_tori)

        if not p.is_dead:
            active_particles.append(p)
            life_norm = p.life / p.max_life
            alpha = int(life_norm * (150 + local_tori * 100))

            # Color shifts from Electric Cyan to Amber near resonance cores
            if local_tori > 0.45:
                cr = int(245)
                cg = int(220 + life_norm * 30)
                cb = int(140 + life_norm * 60)
            else:
                cr = int(80 + life_norm * 60)
                cg = int(240 + life_norm * 15)
                cb = int(225 + life_norm * 30)

            # Spark aura
            py5.no_stroke()
            py5.fill(cr, cg, cb, int(alpha * 0.38))
            py5.circle(p.px, p.py, p.size * 2.8)

            # Spark nucleus
            py5.fill(255, 255, 245, alpha)
            py5.circle(p.px, p.py, p.size * 1.1)

            # Symplectic trajectory filament
            py5.stroke(cr, cg, cb, int(alpha * 0.52))
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
